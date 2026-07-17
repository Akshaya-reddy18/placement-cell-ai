from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Header
from typing import List, Optional, Any
import logging
import asyncio
import hashlib
from datetime import datetime, timezone
import io
import fitz


from pydantic import BaseModel
from backend.schemas.state import (
    StudentInput, AnalysisStatusResponse, JobMatch, 
    ResumeVersion, SkillGapReport, CareerStrategy
)
from backend.utils.ai_utils import call_gemini_text
from backend.db import supabase_client
from backend.graph.placement_graph import run_placement_analysis
from backend.tools.job_scraper import scrape_jobs_serpapi

# Placeholder for agents not yet fully implemented but referenced in Phase 6 instructions
# from backend.agents.interview_agent import run_mock_interview
# from backend.agents.recruiter_simulator import simulate_recruiter_review
# from backend.agents.probability_predictor import predict_placement_probability

router = APIRouter(prefix="/api")
logger = logging.getLogger("api_routes")

STAGE_ORDER = ["wishlist", "applied", "oa", "interview", "offer", "rejected"]


def _current_student_id(client, header_student_id: Optional[str]) -> Optional[str]:
    if header_student_id:
        return header_student_id
    try:
        latest = client.table("students").select("id").order("created_at", desc=True).limit(1).execute()
        if latest.data:
            return latest.data[0].get("id")
    except Exception:
        return None
    return None


def _job_identifier(job: dict) -> str:
    key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('url', '')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _normalize_student_payload(payload: dict) -> dict:
    career_goals = payload.get("career_goals") or payload.get("careerGoals") or {}
    target_companies = payload.get("targetCompanies") or career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
    preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
    skills = payload.get("skills") or career_goals.get("skills") or []

    github_url = payload.get("github_url") or payload.get("githubUrl")
    github_username = payload.get("github_username") or payload.get("githubUsername")
    if not github_url and github_username:
        github_url = f"https://github.com/{github_username}"

    linkedin_url = payload.get("linkedin_url") or payload.get("linkedinUrl")
    resume_url = payload.get("resume_url") or payload.get("resumeUrl") or payload.get("resumeFileName")

    merged_goals = {
        **career_goals,
        "preferred_roles": preferred_roles,
        "preferredRoles": preferred_roles,
        "target_companies": target_companies,
        "targetCompanies": target_companies,
        "skills": skills,
    }

    return {
        "name": payload.get("name"),
        "email": payload.get("email"),
        "college": payload.get("college"),
        "branch": payload.get("branch"),
        "graduation_year": payload.get("graduation_year") or payload.get("graduationYear"),
        "github_url": github_url,
        "linkedin_url": linkedin_url,
        "resume_url": resume_url,
        "resume_text": payload.get("resume_text") or payload.get("resumeText"),
        "career_goals": merged_goals,
    }


def _normalize_job(job: dict, student_data: Optional[dict] = None) -> dict:
    student_skills = {skill.lower() for skill in (student_data or {}).get("skill_graph", {}).keys()}
    requirements = job.get("requirements") or []
    requirements = requirements if isinstance(requirements, list) else [str(requirements)]
    requirement_hits = sum(1 for skill in requirements if str(skill).lower() in student_skills)
    description = job.get("description", "")
    description_hits = sum(1 for skill in student_skills if skill and skill in description.lower())
    match_percentage = min(100, max(10, requirement_hits * 18 + description_hits * 4 + 20))

    return {
        "id": job.get("id") or _job_identifier(job),
        "title": job.get("title", "Unknown Role"),
        "company": job.get("company", "Unknown Company"),
        "location": job.get("location", "Remote"),
        "salary": job.get("salary"),
        "matchPercentage": match_percentage,
        "requirements": requirements,
        "description": description,
        "priority": job.get("priority") or ("high" if match_percentage >= 75 else "medium" if match_percentage >= 50 else "low"),
        "postedAt": job.get("posted_at") or job.get("postedAt") or "Recently",
        "source": job.get("source", "Live Search"),
        "url": job.get("url"),
    }


def _student_context(client, student_id: Optional[str]) -> dict[str, Any]:
    if not student_id:
        return {}
    try:
        student = client.table("students").select("*").eq("id", student_id).execute()
        profile = client.table("student_profiles").select("*").eq("student_id", student_id).execute()
        status = client.table("analysis_status").select("*").eq("student_id", student_id).execute()
        return {
            "student": student.data[0] if student.data else {},
            "profile": profile.data[0] if profile.data else {},
            "status": status.data[0] if status.data else {},
        }
    except Exception:
        return {}


def _fetch_live_jobs(student_data: Optional[dict] = None, query: Optional[str] = None, location: str = "India") -> list[dict]:
    if query:
        role_queries = [query]
    else:
        preferred_roles = (((student_data or {}).get("career_goals") or {}).get("preferred_roles") or ["Software Engineer"])
        role_queries = preferred_roles[:3]

    scraped: list[dict] = []
    seen: set[str] = set()
    for role in role_queries:
        results = scrape_jobs_serpapi.invoke({"query": f"{role} jobs", "location": location}) if False else scrape_jobs_serpapi.invoke(f"{role} jobs in {location}")
        for job in results or []:
            key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('url', '')}"
            if key in seen:
                continue
            seen.add(key)
            scraped.append(_normalize_job(job, student_data))

    saved_jobs: list[dict] = []
    for job in scraped:
        try:
            saved = supabase_client.save_job({
                "title": job["title"],
                "company": job["company"],
                "source": job.get("source"),
                "url": job.get("url"),
                "description": job.get("description"),
                "requirements": job.get("requirements"),
                "location": job.get("location"),
                "experience_level": job.get("priority"),
                "posted_at": job.get("postedAt"),
                "is_active": True,
            })
            saved_jobs.append({**job, "id": saved.get("id", job["id"])})
        except Exception:
            saved_jobs.append(job)
    return saved_jobs


def _analysis_status_payload(student_id: Optional[str], client) -> dict:
    if student_id:
        result = client.table("analysis_status").select("*").eq("student_id", student_id).execute()
        if result.data:
            row = result.data[0]
            return {
                "student_id": student_id,
                "current_agent": row.get("current_agent") or "idle",
                "percentage": int(row.get("percentage") or 0),
                "status": row.get("status") or "idle",
                "completed_agents": row.get("completed_agents") or [],
            }
    return {
        "student_id": student_id or "demo",
        "current_agent": "idle",
        "percentage": 0,
        "status": "idle",
        "completed_agents": [],
    }


def _get_applications(client, student_id: Optional[str]) -> list[dict]:
    try:
        if student_id:
            result = client.table("applications").select("*").eq("student_id", student_id).execute()
        else:
            result = client.table("applications").select("*").execute()
    except Exception:
        return []

    applications = []
    for row in result.data or []:
        applications.append({
            **row,
            "stage": row.get("stage") or row.get("status") or "applied",
            "status": row.get("status") or row.get("stage") or "applied",
        })
    return applications


def _tracker_payload(student_id: Optional[str], client) -> dict:
    applications = _get_applications(client, student_id)
    stage_counts = {stage: 0 for stage in STAGE_ORDER}
    for app in applications:
        stage = str(app.get("stage") or app.get("status") or "applied").lower()
        if stage in stage_counts:
            stage_counts[stage] += 1
        else:
            stage_counts.setdefault(stage, 0)
            stage_counts[stage] += 1

    total = max(len(applications), 1)
    conversion = {
        "applyToOa": round((stage_counts["oa"] / total) * 100),
        "oaToInterview": round((stage_counts["interview"] / max(stage_counts["oa"], 1)) * 100),
        "interviewToOffer": round((stage_counts["offer"] / max(stage_counts["interview"], 1)) * 100),
    }
    return {
        "applications": applications,
        "analytics": {
            "byStage": [{"stage": stage.title(), "count": count} for stage, count in stage_counts.items()],
            "conversionRates": conversion,
        },
    }


def _resume_payload(student_id: Optional[str], client) -> dict:
    versions = supabase_client.get_resume_versions(student_id) if student_id else []
    latest = versions[0] if versions else {}
    missing = latest.get("missing_keywords") or []
    present = latest.get("present_keywords") or []
    suggestions = latest.get("suggestions") or []
    ats = int(latest.get("ats_score") or 0)
    overall = min(100, max(0, ats))
    return {
        "scores": {
            "ats": overall,
            "keyword": min(100, len(present) * 12) if present else 0,
            "formatting": 0,
            "impact": 0,
            "overall": overall,
        },
        "missingKeywords": missing,
        "presentKeywords": present,
        "suggestions": suggestions,
        "optimizedSummary": latest.get("optimized_resume_text") or "",
        "originalExcerpt": latest.get("original_resume_text") or "",
        "optimizedExcerpt": latest.get("optimized_resume_text") or "",
        "checklist": [],
    }


def _interview_payload(student_id: Optional[str], client) -> dict:
    sessions = supabase_client.get_interview_sessions(student_id) if student_id else []
    latest = sessions[0] if sessions else {}
    questions_bank = latest.get("questions_bank") or {}
    tech_questions = questions_bank.get("technical") or []
    hr_questions = questions_bank.get("hr") or []
    readiness = int(latest.get("readiness_score") or 0)
    confidence = int(latest.get("confidence_score") or 0)
    weak = latest.get("weak_areas") or []
    strong = latest.get("strong_areas") or []
    return {
        "readinessScore": readiness,
        "confidenceScore": confidence,
        "technicalQuestions": [
            {
                "id": f"t{index + 1}",
                "question": item.get("question") if isinstance(item, dict) else str(item),
                "type": "technical",
                "difficulty": (item.get("difficulty") if isinstance(item, dict) else "medium") or "medium",
                "topic": (item.get("topic") if isinstance(item, dict) else "Technical") or "Technical",
            }
            for index, item in enumerate(tech_questions)
        ],
        "behavioralQuestions": [
            {
                "id": f"b{index + 1}",
                "question": item.get("question") if isinstance(item, dict) else str(item),
                "type": "hr",
                "difficulty": (item.get("difficulty") if isinstance(item, dict) else "medium") or "medium",
                "topic": (item.get("topic") if isinstance(item, dict) else "Behavioral") or "Behavioral",
            }
            for index, item in enumerate(hr_questions)
        ],
        "mockSessions": [
            {"id": session.get("id", f"m{index+1}"), "title": session.get("session_type", "Prep Session"), "date": session.get("created_at", ""), "score": int(session.get("readiness_score") or 0), "questionsCount": len(session.get("questions_bank") or {})}
            for index, session in enumerate(sessions[:5])
        ],
        "weakAreas": weak,
        "strongAreas": strong,
        "feedback": latest.get("feedback", ""),
    }


def _career_payload(student_id: Optional[str], client) -> dict:
    strategy = supabase_client.get_career_strategy(student_id) if student_id else None
    profile = client.table("student_profiles").select("*").eq("student_id", student_id).execute() if student_id else None
    target_companies = (strategy or {}).get("target_companies") or []
    if isinstance(target_companies, str):
        target_companies = [target_companies]
    focus = (strategy or {}).get("focus_recommendation") or (profile.data[0].get("career_profile", {}) if profile and profile.data else {}).get("summary") or ""
    probability = float((strategy or {}).get("placement_probability") or 0)
    return {
        "focusRecommendation": focus if isinstance(focus, str) else str(focus),
        "placementProbability": probability,
        "targetCompanies": target_companies[:10],
        "milestones": [],
        "skillGaps": [{"skill": skill, "priority": "critical", "marketDemand": 0} for skill in ((strategy or {}).get("red_flags") or [])[:3]],
        "learningRecommendations": (strategy or {}).get("quick_wins") or [],
        "marketInsights": [],
        "packageProjection": {"min": 0, "max": 0},
    }


def _dashboard_payload(student_id: Optional[str], client) -> dict:
    tracker = _tracker_payload(student_id, client)
    resume = _resume_payload(student_id, client)
    interview = _interview_payload(student_id, client)
    career = _career_payload(student_id, client)
    jobs = _fetch_live_jobs(_student_context(client, student_id).get("profile", {}), None)[:3]
    applications = tracker["applications"]
    metrics = {
        "applications": len(applications),
        "resumeScore": resume["scores"]["overall"],
        "interviewReadiness": interview["readinessScore"],
        "placementProbability": int(career["placementProbability"] or 0),
        "placementReadiness": round((resume["scores"]["overall"] + interview["readinessScore"] + int(career["placementProbability"] or 0)) / 3),
    }
    insights = []
    deadlines = [
        {"id": app.get("id", str(index + 1)), "title": app.get("role", app.get("stage", "Application")), "company": app.get("company", ""), "dueDate": app.get("applied_at", app.get("date", ""))[:10] if app.get("applied_at") or app.get("date") else "", "type": "application"}
        for index, app in enumerate(applications[:3])
    ]
    chart_data = [{"name": item["stage"], "applications": item["count"], "interviews": 0} for item in tracker["analytics"]["byStage"]]
    readiness_breakdown = [
        {"name": "Technical", "value": interview["readinessScore"]},
        {"name": "Resume", "value": resume["scores"]["overall"]},
        {"name": "Career Fit", "value": int(career["placementProbability"] or 0)},
        {"name": "Pipeline", "value": min(100, len(applications) * 12)},
    ]
    return {
        "metrics": metrics,
        "insights": insights,
        "deadlines": deadlines,
        "recommendedJobs": jobs,
        "chartData": chart_data,
        "readinessBreakdown": readiness_breakdown,
    }

@router.post("/students", response_model=dict)
async def create_student(student: StudentInput):
    """Create a student record and initialize analysis status."""
    client = supabase_client.get_supabase_client()
    try:
        student_data = _normalize_student_payload(student.model_dump())
        result = client.table("students").upsert(student_data, on_conflict="email").execute()
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create student")
        
        student_id = result.data[0]["id"]
        
        # Initialize status
        supabase_client.update_analysis_status(
            student_id, "starting", [], 0, "pending"
        )
        
        return {"student_id": student_id, "message": "Student created successfully"}
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding", response_model=dict)
async def onboarding(payload: dict):
    client = supabase_client.get_supabase_client()
    student_data = _normalize_student_payload(payload)
    try:
        result = client.table("students").upsert(student_data, on_conflict="email").execute()
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create student")

        student_id = result.data[0].get("id")
        supabase_client.update_analysis_status(student_id, "starting", [], 0, "pending")
        return {"student_id": student_id, "message": "Student created successfully"}
    except Exception as e:
        logger.error(f"Error onboarding student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboarding")
async def get_onboarding(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    if not student_id:
        raise HTTPException(status_code=404, detail="Student not found")
    student = client.table("students").select("*").eq("id", student_id).execute()
    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")
    return student.data[0]


@router.get("/dashboard")
async def get_dashboard(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    return _dashboard_payload(student_id, client)


@router.get("/status")
async def get_current_status(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    return _analysis_status_payload(student_id, client)

@router.post("/analyze/{student_id}")
async def start_analysis(student_id: str, background_tasks: BackgroundTasks):
    """Start the background analysis pipeline."""
    client = supabase_client.get_supabase_client()
    student_res = client.table("students").select("*").eq("id", student_id).execute()
    if not student_res.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_data = student_res.data[0]
    
    # Run in background
    background_tasks.add_task(run_placement_analysis, student_id, student_data)
    
    return {"message": "Analysis started in background"}

@router.get("/status/{student_id}", response_model=AnalysisStatusResponse)
async def get_status(student_id: str):
    """Poll the analysis progress."""
    client = supabase_client.get_supabase_client()
    result = client.table("analysis_status").select("*").eq("student_id", student_id).execute()
    if not result.data:
        return _analysis_status_payload(student_id, client)
    return result.data[0]

@router.get("/profile/{student_id}")
async def get_profile(student_id: str):
    """Get the full student profile including skills and domain scores."""
    client = supabase_client.get_supabase_client()
    student = client.table("students").select("*").eq("id", student_id).execute()
    profile = client.table("student_profiles").select("*").eq("student_id", student_id).execute()
    
    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return {
        "student": student.data[0],
        "profile": profile.data[0] if profile.data else None
    }

@router.get("/jobs/{student_id}")
async def get_jobs(student_id: str):
    """Get matched jobs for a student."""
    matches = supabase_client.get_job_matches(student_id)
    return matches


@router.get("/jobs")
async def get_live_jobs(
    search: Optional[str] = None,
    location: str = "India",
    x_student_id: Optional[str] = Header(None, alias="X-Student-Id"),
):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    context = _student_context(client, student_id)
    student_profile = context.get("profile") or {}
    jobs = _fetch_live_jobs(student_profile, search, location)
    return jobs

@router.get("/resume/{student_id}")
async def get_resume_versions(student_id: str):
    """Get optimized resume versions."""
    versions = supabase_client.get_resume_versions(student_id)
    return versions


@router.get("/resume")
async def get_resume(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    return _resume_payload(student_id, client)

@router.get("/skills/{student_id}")
async def get_skill_gaps(student_id: str):
    """Get skill gap analysis and roadmap."""
    gaps = supabase_client.get_skill_gaps(student_id)
    if not gaps:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found")
    return gaps

@router.get("/interview/{student_id}")
async def get_interview_prep(student_id: str):
    """Get interview questions and readiness scores."""
    sessions = supabase_client.get_interview_sessions(student_id)
    return sessions


@router.get("/interview")
async def get_interview(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    return _interview_payload(student_id, client)

class ChatPayload(BaseModel):
    history: list[dict]
    student_id: Optional[str] = None

@router.post("/interview/chat")
async def chat_interview(payload: ChatPayload):
    prompt = "You are an expert technical interviewer conducting a mock interview with a candidate. Keep your responses conversational, concise, and professional. Ask one question at a time.\n\nConversation history:\n"
    for msg in payload.history:
        role = "Interviewer" if msg.get("role") == "assistant" else "Candidate"
        prompt += f"{role}: {msg.get('content')}\n"
    prompt += "Interviewer:"
    
    reply = call_gemini_text(prompt, default="Could you elaborate on that?", temperature=0.7)
    return {"reply": reply}

@router.get("/referrals/{student_id}")
async def get_referrals(student_id: str):
    """Get referral strategies."""
    client = supabase_client.get_supabase_client()
    result = client.table("referrals").select("*").eq("student_id", student_id).execute()
    return result.data

@router.get("/strategy/{student_id}")
async def get_career_strategy(student_id: str):
    """Get the comprehensive career strategy."""
    strategy = supabase_client.get_career_strategy(student_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Career strategy not found")
    return strategy


@router.get("/career")
async def get_career(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    return _career_payload(student_id, client)

@router.get("/tracking/{student_id}")
async def get_tracking_dashboard(student_id: str):
    """Get the application tracking dashboard data."""
    client = supabase_client.get_supabase_client()
    try:
        return _tracker_payload(student_id, client)
    except Exception as e:
        logger.error(f"Error loading tracking dashboard for {student_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracker")
async def get_tracker(x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, x_student_id)
    return _tracker_payload(student_id, client)


@router.put("/tracker/{application_id}")
async def update_tracker_application(application_id: str, payload: dict, x_student_id: Optional[str] = Header(None, alias="X-Student-Id")):
    client = supabase_client.get_supabase_client()
    stage = payload.get("stage") if isinstance(payload, dict) else None
    if not stage:
        raise HTTPException(status_code=400, detail="stage is required")
    student_id = _current_student_id(client, x_student_id)
    result = client.table("applications").select("*").eq("id", application_id).execute()
    record = result.data[0] if result.data else {"id": application_id, "student_id": student_id, "job_id": application_id}
    if student_id and not record.get("student_id"):
        record["student_id"] = student_id
    record["stage"] = stage
    record["status"] = stage
    record["last_updated"] = datetime.now(timezone.utc).isoformat()
    saved = client.table("applications").upsert(record, on_conflict="id").execute()
    return saved.data[0] if saved.data else record

@router.put("/application/{student_id}")
async def update_application(student_id: str, job_id: str, status: str):
    """Update application status."""
    client = supabase_client.get_supabase_client()
    result = client.table("applications").upsert({
        "student_id": student_id,
        "job_id": job_id,
        "status": status,
        "stage": status,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="student_id,job_id").execute()
    return result.data[0] if result.data else {"message": "Updated"}


@router.post("/apply/{student_id}/{job_id}")
async def apply_to_job(student_id: str, job_id: str):
    client = supabase_client.get_supabase_client()
    result = client.table("applications").upsert({
        "student_id": student_id,
        "job_id": job_id,
        "status": "applied",
        "stage": "applied",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="student_id,job_id").execute()
    return result.data[0] if result.data else {"message": "Applied"}

@router.post("/upload-resume/{student_id}")
async def upload_resume(student_id: str, file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF resume."""
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        
        client = supabase_client.get_supabase_client()
        
        # Update the student profile
        client.table("student_profiles").update({"resume_text": text}).eq("student_id", student_id).execute()
        
        # We need to trigger the ATS agent in the background
        # For simplicity in this endpoint, we'll re-run the placement analysis 
        # (or just the ats agent part if we had a dedicated graph entry point)
        if background_tasks:
            # We fetch the current profile to pass to the graph
            result = client.table("student_profiles").select("*").eq("student_id", student_id).execute()
            if result.data:
                background_tasks.add_task(run_placement_analysis, student_id, result.data[0])
                
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse resume")
    return {"filename": file.filename, "message": "Resume uploaded and processing started"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

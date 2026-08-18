from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Header, Request
from typing import List, Optional, Any
import logging
import asyncio
import hashlib
import json
from datetime import datetime, timezone
import io
try:
    import fitz
except ImportError:
    fitz = None


from pydantic import BaseModel
from backend.schemas.state import (
    StudentInput, AnalysisStatusResponse, JobMatch, 
    ResumeVersion, SkillGapReport, CareerStrategy,
    ChatPayload
)
from backend.utils.ai_utils import call_gemini_text, call_gemini_json
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


def _current_student_id(client, request_headers: dict) -> Optional[str]:
    # Try to get token from Authorization header
    auth_header = request_headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "").strip() if "Bearer " in auth_header else None
    
    if not token:
        # Fallback to custom header for development if absolutely needed
        token = request_headers.get("x-supabase-auth")
        
    if token:
        if token == "guest_token":
            return "00000000-0000-0000-0000-000000000000"
        try:
            user_res = client.auth.get_user(token)
            if user_res and user_res.user:
                user_id = user_res.user.id
                
                # Resolve student record from auth.users.id
                student_res = client.table("students").select("id").eq("user_id", user_id).execute()
                if student_res.data:
                    return student_res.data[0]["id"]
                
                # Check if user_id is the primary key id
                direct_res = client.table("students").select("id").eq("id", user_id).execute()
                if direct_res.data:
                    return direct_res.data[0]["id"]
        except Exception as e:
            pass
            
    return None



def _job_identifier(job: dict) -> str:
    key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('url', '')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _normalize_student_payload(payload: dict) -> dict:
    career_goals = payload.get("career_goals") or payload.get("careerGoals") or {}
    target_companies = payload.get("targetCompanies") or career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
    preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
    skills = payload.get("skills") or career_goals.get("skills") or []
    
    # Normalize experience level from both snake_case and camelCase
    experience_level = (
        career_goals.get("experience_level")
        or career_goals.get("experienceLevel")
        or payload.get("experience_level")
        or payload.get("experienceLevel")
        or ""
    )

    github_url = payload.get("github_url") or payload.get("githubUrl")
    github_username = payload.get("github_username") or payload.get("githubUsername")
    if not github_url and github_username:
        github_url = f"https://github.com/{github_username}"

    linkedin_url = payload.get("linkedin_url") or payload.get("linkedinUrl")
    resume_url = payload.get("resume_url") or payload.get("resumeUrl") or payload.get("resumeFileName")
    
    # Normalize locations and work modes from both naming conventions
    locations = (
        career_goals.get("locations")
        or []
    )
    work_modes = (
        career_goals.get("workModes")
        or career_goals.get("work_modes")
        or []
    )
    employment_types = (
        career_goals.get("employmentTypes")
        or career_goals.get("employment_types")
        or []
    )
    company_types = (
        career_goals.get("companyTypes")
        or career_goals.get("company_types")
        or []
    )

    merged_goals = {
        **career_goals,
        "preferred_roles": preferred_roles,
        "preferredRoles": preferred_roles,
        "target_companies": target_companies,
        "targetCompanies": target_companies,
        "skills": skills,
        "experience_level": experience_level,
        "experienceLevel": experience_level,
        "locations": locations,
        "work_modes": work_modes,
        "employment_types": employment_types,
        "company_types": company_types,
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


def _score_job(job: dict, student_data: Optional[dict]) -> tuple[int, str]:
    if not student_data:
        return 50, "Average match based on general job profile."

    career_goals = student_data.get("career_goals") or {}
    
    # Safely gather skills from various places:
    # 1) career_goals.skills (from students table)
    # 2) skill_graph keys (from student_profiles table, merged into student_data_for_scoring)
    student_skills = set()
    for s in career_goals.get("skills", []):
        student_skills.add(str(s).lower())
    for s in (student_data.get("skill_graph") or {}).keys():
        student_skills.add(str(s).lower())
        
    # 1. Base requirements and skills (Max 40 points)
    requirements = job.get("requirements") or []
    requirements = requirements if isinstance(requirements, list) else [str(requirements)]
    requirement_hits = sum(1 for skill in requirements if str(skill).lower() in student_skills)
    
    desc_lower = job.get("description", "").lower()
    description_hits = sum(1 for skill in student_skills if skill and skill in desc_lower)
    
    skill_score = min(40, requirement_hits * 10 + description_hits * 2)
    
    # 2. Company preference (Max 10 points — optional, not mandatory)
    company_score = 0
    target_companies = [c.lower() for c in (
        career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
    )]
    if job.get("company", "").lower() in target_companies:
        company_score = 10
        
    # 3. Role preference (Max 20 points)
    role_score = 0
    preferred_roles = [r.lower() for r in (
        career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
    )]
    job_title = job.get("title", "").lower()
    if any(r in job_title for r in preferred_roles):
        role_score = 20
    elif any(r in job_title for r in ["engineer", "developer", "scientist", "analyst", "architect"]):
        role_score = 8

    # 4. Location preference (Max 15 points)
    loc_score = 0
    locations = [l.lower() for l in (career_goals.get("locations") or [])]
    job_loc = job.get("location", "").lower()
    if "remote" in job_loc:
        loc_score = 15
    elif any(l in job_loc for l in locations):
        loc_score = 15
        
    # 5. Experience preference (Max 15 points, with penalty for mismatch)
    exp_score = 0
    student_exp = (
        career_goals.get("experience_level")
        or career_goals.get("experienceLevel")
        or ""
    ).lower()
    job_exp = (job.get("experience_level") or "").lower()
    
    if student_exp in ("fresher", "0-1 years"):
        if "intern" in job_title or "entry" in job_exp or "graduate" in job_title or "fresher" in job_exp:
            exp_score = 15
        elif "senior" in job_title or "lead" in job_title or "principal" in job_title:
            exp_score = -15  # penalize heavily
    elif student_exp in ("2-3 years",):
        if "senior" not in job_title and "lead" not in job_title and "intern" not in job_title:
            exp_score = 10
        elif "intern" in job_title:
            exp_score = -15
    elif student_exp in ("3+ years",):
        if "senior" in job_title or "lead" in job_title or "staff" in job_title:
            exp_score = 15
        elif "intern" in job_title:
            exp_score = -15

    total_score = min(99, max(10, skill_score + company_score + role_score + loc_score + exp_score))
    
    # Generate human-readable reason
    reasons = []
    if company_score > 0:
        reasons.append("It is one of your target companies.")
    if role_score == 20:
        reasons.append("The role aligns with your preferred career goals.")
    if requirement_hits > 0:
        matched = [s for s in requirements if str(s).lower() in student_skills][:3]
        if matched:
            reasons.append(f"Strong alignment with your skills in {', '.join(matched)}.")
    elif description_hits > 0:
        matched_desc = sorted([s for s in student_skills if s and s in desc_lower])[:3]
        if matched_desc:
            reasons.append(f"Your skills ({', '.join(matched_desc)}) are mentioned in the job description.")
    if exp_score == 15:
        reasons.append("This role matches your experience level.")
    
    reason = " ".join(reasons) if reasons else "Good general fit based on your overall profile."
    
    return total_score, reason


def _normalize_job(job: dict, student_data: Optional[dict] = None) -> dict:
    match_percentage, match_reason = _score_job(job, student_data)
    
    # Ensure apply_url is properly extracted
    apply_url = job.get("apply_url") or job.get("job_url") or job.get("url")
    
    return {
        "id": job.get("id") or _job_identifier(job),
        "title": job.get("title", "Unknown Role"),
        "company": job.get("company", "Unknown Company"),
        "location": job.get("location", "Remote"),
        "salary": job.get("salary"),
        "matchPercentage": match_percentage,
        "matchReason": match_reason,
        "requirements": job.get("requirements") or [],
        "description": job.get("description", ""),
        "priority": job.get("priority") or ("high" if match_percentage >= 75 else "medium" if match_percentage >= 50 else "low"),
        "postedAt": job.get("posted_at") or job.get("postedAt") or "Recently",
        "source": job.get("source", "Live Search"),
        "url": apply_url,
        "job_url": apply_url,
        "apply_url": apply_url,
        "work_mode": job.get("work_mode"),
        "employment_type": job.get("employment_type"),
        "company_type": job.get("company_type"),
        "industry": job.get("industry"),
        "is_verified": job.get("is_verified", True),
    }

def _student_context(client, student_id: Optional[str]) -> dict:
    if not student_id:
        return {}
    try:
        student = client.table("students").select("*").eq("id", student_id).execute()
        profile = client.table("student_profiles").select("*").eq("student_id", student_id).execute()
        status = client.table("analysis_status").select("*").eq("student_id", student_id).execute()
        student_row = student.data[0] if student.data else {}
        profile_row = profile.data[0] if profile.data else {}
        return {
            "student": student_row,
            "profile": profile_row,
            "status": status.data[0] if status.data else {},
            # Merged view: career_goals from students table, skill_graph from student_profiles table
            "career_goals": student_row.get("career_goals") or {},
            "skill_graph": profile_row.get("skill_graph") or {},
        }
    except Exception as e:
        logger.error(f"Error loading student context for {student_id}: {e}")
        return {}

def _fetch_live_jobs(context: Optional[dict] = None, filters: dict = None) -> list[dict]:
    """
    Fetch, filter, score and rank jobs for a specific authenticated student.
    
    `context` is the dict returned by _student_context(), containing:
      - context["career_goals"]  → from students table (preferred_roles, locations, experience_level, etc.)
      - context["skill_graph"]   → from student_profiles table (skill -> score mapping)
      - context["student"]       → full students row
    """
    filters = filters or {}
    context = context or {}
    
    # career_goals lives in the students table — NOT in student_profiles
    career_goals = context.get("career_goals") or (context.get("student") or {}).get("career_goals") or {}
    skill_graph = context.get("skill_graph") or (context.get("profile") or {}).get("skill_graph") or {}
    
    logger.info(f"[jobs] career_goals keys: {list(career_goals.keys())}")
    logger.info(f"[jobs] preferred_roles: {career_goals.get('preferred_roles')}")
    logger.info(f"[jobs] locations: {career_goals.get('locations')}")
    logger.info(f"[jobs] skill_graph skills: {list(skill_graph.keys())[:10]}")

    # Build merged student_data for scoring (skill_graph merged into career_goals dict)
    student_data_for_scoring = {
        "career_goals": career_goals,
        "skill_graph": skill_graph,
    }

    # 1. Determine search constraints from query params OR student profile
    search_q = filters.get("search", "").lower()
    
    # Roles: from filter param → else from profile preferredRoles
    filter_roles_raw = filters.get("roles", "")
    if filter_roles_raw:
        filter_roles = [r.strip().lower() for r in filter_roles_raw.split(",") if r.strip()]
    else:
        filter_roles = [r.lower() for r in career_goals.get("preferred_roles", [])]

    # Locations: from filter param → else from profile
    filter_locs_raw = filters.get("locations", "")
    if filter_locs_raw:
        filter_locs = [l.strip().lower() for l in filter_locs_raw.split(",") if l.strip()]
    else:
        filter_locs = [l.lower() for l in career_goals.get("locations", [])]

    # UI-selected hard filters (explicit selections only)
    ui_work_modes = [w.strip().lower() for w in filters.get("workModes", "").split(",") if w.strip()]
    ui_emp_types = [e.strip().lower() for e in filters.get("employmentTypes", "").split(",") if e.strip()]
    ui_comp_types = [c.strip().lower() for c in filters.get("companyTypes", "").split(",") if c.strip()]

    # Build scraper queries from the student's ACTUAL profile roles and locations
    scrape_roles = filter_roles or ["software engineer"]
    scrape_locs = filter_locs or ["india"]

    # 2. Fetch all active jobs from DB
    try:
        db_client = supabase_client.get_supabase_client()
        db_jobs = db_client.table("jobs").select("*").eq("is_active", True).execute().data or []
        logger.info(f"[jobs] fetched {len(db_jobs)} jobs from DB")
    except Exception as e:
        logger.error(f"[jobs] DB fetch failed: {e}")
        db_jobs = []

    # 3. Apply search and explicit UI filters (only if user explicitly selected them)
    def _matches_hard_filters(job: dict) -> bool:
        # Search text filter (title/company)
        if search_q:
            if search_q not in job.get("title", "").lower() and search_q not in job.get("company", "").lower():
                return False
        # Work mode: only filter if user explicitly selected via UI chips
        if ui_work_modes and job.get("work_mode"):
            if job["work_mode"].lower() not in ui_work_modes:
                return False
        # Employment type: only filter if user explicitly selected
        if ui_emp_types and job.get("employment_type"):
            if job["employment_type"].lower() not in ui_emp_types:
                return False
        # Company type: only filter if user explicitly selected
        if ui_comp_types and job.get("company_type"):
            if job["company_type"].lower() not in ui_comp_types:
                return False
        return True

    hard_filtered = [j for j in db_jobs if _matches_hard_filters(j)]
    logger.info(f"[jobs] {len(hard_filtered)} jobs after hard filters")

    # 4. Apply soft role+location filter (scoring preference, not hard exclusion)
    #    Try strict filter first. If it yields zero results, fall back to all hard-filtered jobs.
    def _role_loc_match(job: dict) -> bool:
        j_title = job.get("title", "").lower()
        j_loc = job.get("location", "").lower()
        role_ok = not filter_roles or any(r in j_title for r in filter_roles)
        loc_ok = not filter_locs or any(l in j_loc for l in filter_locs) or "remote" in j_loc
        return role_ok and loc_ok

    role_loc_filtered = [j for j in hard_filtered if _role_loc_match(j)]
    logger.info(f"[jobs] {len(role_loc_filtered)} jobs after role+location soft filter")

    # Use role+loc filtered if we have results; otherwise fall back
    candidate_db_jobs = role_loc_filtered if role_loc_filtered else hard_filtered

    # 5. Scrape live jobs if DB doesn't have enough
    if len(candidate_db_jobs) < 10:
        seen_keys = {f"{j.get('title', '')}-{j.get('company', '')}" for j in db_jobs}
        target_companies = career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
        
        queries = []
        if target_companies:
            queries.append(f"{scrape_roles[0]} at {target_companies[0]}")
        for role in scrape_roles[:2]:
            for loc in scrape_locs[:1]:
                queries.append(f"{role} jobs in {loc}")
        
        logger.info(f"[jobs] Scraping live jobs with queries: {queries[:3]}")
        
        for q in list(dict.fromkeys(queries))[:3]:
            try:
                results = scrape_jobs_serpapi.invoke(q)
                logger.info(f"[jobs] Scraped {len(results or [])} jobs for query '{q}'")
                for job in results or []:
                    key = f"{job.get('title', '')}-{job.get('company', '')}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    # Verify URL
                    apply_url = job.get("apply_url") or job.get("job_url") or job.get("url") or ""
                    if not apply_url:
                        continue
                    try:
                        saved = supabase_client.save_job({
                            "title": job.get("title", ""),
                            "company": job.get("company", ""),
                            "source": job.get("source", ""),
                            "url": apply_url,
                            "description": job.get("description", ""),
                            "requirements": job.get("requirements", []),
                            "location": job.get("location", ""),
                            "posted_at": job.get("posted_at") or job.get("postedAt") or "",
                            "work_mode": job.get("work_mode", ""),
                            "employment_type": job.get("employment_type", ""),
                            "company_type": job.get("company_type", ""),
                            "is_active": True,
                        })
                        candidate_db_jobs.append({**job, "id": saved.get("id", job.get("id", ""))})
                    except Exception as save_err:
                        logger.warning(f"[jobs] Could not save scraped job: {save_err}")
                        candidate_db_jobs.append(job)
            except Exception as scrape_err:
                logger.warning(f"[jobs] Scrape failed for query '{q}': {scrape_err}")

    logger.info(f"[jobs] {len(candidate_db_jobs)} candidate jobs before scoring")

    # 6. Score and normalize each job for THIS specific student
    personalized_jobs = []
    for job in candidate_db_jobs:
        # Only include jobs with valid apply URLs
        apply_url = job.get("apply_url") or job.get("job_url") or job.get("url") or ""
        if not apply_url or "google.com/search" in apply_url or "bing.com/search" in apply_url:
            continue
        norm = _normalize_job(job, student_data_for_scoring)
        personalized_jobs.append(norm)

    personalized_jobs.sort(key=lambda x: x.get("matchPercentage", 0), reverse=True)
    logger.info(f"[jobs] returning {len(personalized_jobs)} personalized jobs")
    return personalized_jobs


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
                "error_message": row.get("error_message"),
            }
    return {
        "student_id": student_id or "demo",
        "current_agent": "idle",
        "percentage": 0,
        "status": "idle",
        "completed_agents": [],
        "error_message": None,
    }


def _get_applications(client, student_id: Optional[str]) -> list[dict]:
    try:
        if student_id:
            result = client.table("applications").select("*").eq("student_id", student_id).execute()
        else:
            return []
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
    context = _student_context(client, student_id) if student_id else {}
    student_row = context.get("student") or {}
    resume_text = student_row.get("resume_text") or ""
    career_goals = context.get("career_goals") or student_row.get("career_goals") or {}
    preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
    target_role = preferred_roles[0] if preferred_roles else "Software Engineer"
    target_companies = career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
    target_company = target_companies[0] if target_companies else "Tech Industry"

    versions = supabase_client.get_resume_versions(student_id) if student_id else []

    # If no resume versions exist yet but we have uploaded resume_text, analyze it immediately for the target role
    if not versions and resume_text:
        try:
            from backend.tools.ats_tool import analyze_ats_compatibility, generate_optimized_resume
            from backend.utils.ai_utils import simple_tokens
            general_jd = f"Seeking an experienced {target_role} proficient in modern engineering frameworks, software design, core technical stacks, and collaborative problem-solving for {target_company}."
            
            ats_result = analyze_ats_compatibility.invoke({
                "resume_text": resume_text,
                "job_description": general_jd,
                "job_title": target_role,
                "company": target_company
            })
            if not isinstance(ats_result, dict):
                ats_result = {}

            job_terms = {term.lower() for term in simple_tokens(general_jd)[:30]}
            resume_terms = {term.lower() for term in simple_tokens(resume_text)}
            overlap = job_terms & resume_terms

            ats_score = int(ats_result.get("ats_score") or min(100, max(45, len(overlap) * 8 + 45)))
            missing_kw = ats_result.get("missing_keywords") or sorted(list(job_terms - resume_terms))[:8]
            present_kw = ats_result.get("present_keywords") or sorted(list(overlap))[:8]
            suggestions = ats_result.get("suggestions") or [
                f"Highlight core {target_role} project implementations and technical leadership.",
                "Quantify impact with concrete metrics (performance improvements, uptime, scale).",
                f"Include industry keywords and technical skills relevant to {target_role}."
            ]

            optimized_text = ats_result.get("optimized_summary") or ats_result.get("optimized_resume")
            if not optimized_text or len(str(optimized_text)) < 50:
                try:
                    optimized_text = generate_optimized_resume.invoke({
                        "original_resume": resume_text,
                        "job_description": general_jd,
                        "ats_analysis": ats_result
                    })
                except Exception:
                    optimized_text = resume_text

            version = {
                "ats_score": ats_score,
                "missing_keywords": missing_kw,
                "present_keywords": present_kw,
                "suggestions": suggestions,
                "optimized_resume_text": str(optimized_text) if optimized_text else resume_text,
                "original_resume_text": resume_text,
                "target_role": target_role,
                "company": target_company
            }
            if student_id:
                supabase_client.save_resume_version(student_id, "target_role", version)
            versions = [version]
        except Exception as e:
            logger.error(f"Error in on-demand resume analysis for target role {target_role}: {e}")

    latest = versions[0] if versions else {}
    missing = latest.get("missing_keywords") or []
    present = latest.get("present_keywords") or []
    suggestions = latest.get("suggestions") or []
    ats = int(latest.get("ats_score") or 0)
    overall = min(100, max(0, ats)) if ats > 0 else (75 if resume_text else 0)

    original_text = latest.get("original_resume_text") or resume_text or ""
    optimized_text = latest.get("optimized_resume_text") or latest.get("optimizedSummary") or original_text

    keyword_score = min(100, max(25, len(present) * 12)) if present else (70 if resume_text else 0)
    formatting_score = min(100, max(65, 100 - len(latest.get("formatting_issues", [])) * 10)) if (resume_text or versions) else 0
    impact_score = min(100, max(50, ats - 5)) if ats > 0 else (72 if resume_text else 0)

    checklist = [
        {"id": "c1", "label": f"Tailor keywords for {target_role}", "done": len(missing) == 0},
        {"id": "c2", "label": "Quantify project and work achievements", "done": overall > 70},
        {"id": "c3", "label": "ATS friendly single-column format", "done": formatting_score >= 80},
        {"id": "c4", "label": f"Highlight core tech stack for {target_role}", "done": len(present) >= 3},
        {"id": "c5", "label": "Highlight domain experience & projects", "done": overall > 60},
    ] if (resume_text or versions) else []

    return {
        "scores": {
            "ats": overall,
            "keyword": keyword_score,
            "formatting": formatting_score,
            "impact": impact_score,
            "overall": overall,
        },
        "missingKeywords": missing,
        "presentKeywords": present,
        "suggestions": suggestions,
        "optimizedSummary": latest.get("optimized_summary") or (optimized_text[:300] if optimized_text else ""),
        "originalExcerpt": original_text,
        "optimizedExcerpt": optimized_text,
        "checklist": checklist,
        "targetRole": target_role,
        "targetCompany": target_company,
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


def _generate_personalized_career_strategy(student_id: Optional[str], context: dict) -> dict:
    student = context.get("student") or {}
    profile = context.get("profile") or {}
    career_goals = context.get("career_goals") or student.get("career_goals") or {}
    candidate_name = student.get("name") or "Candidate"
    branch = student.get("branch") or "Computer Science & Engineering"
    college = student.get("college") or "Engineering Institute"
    
    preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
    target_role = preferred_roles[0] if preferred_roles else "Software Engineer"
    
    target_companies = career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
    if not target_companies:
        target_companies = ["Google", "Microsoft", "Amazon", "Flipkart"]
    
    skills = []
    for s in career_goals.get("skills", []):
        skills.append(str(s))
    for s in (context.get("skill_graph") or {}).keys():
        if s not in skills:
            skills.append(str(s))
    if not skills:
        skills = ["Python", "Data Structures", "Web Development", "SQL"]

    exp_level = career_goals.get("experience_level") or career_goals.get("experienceLevel") or "Fresher"
    locations = career_goals.get("locations") or ["Bangalore", "Hyderabad", "Remote"]
    salary_exp = career_goals.get("salary_expectation") or career_goals.get("salaryExpectation") or "12-18 LPA"

    companies_str = ", ".join(target_companies[:4])
    roles_str = ", ".join(preferred_roles) if preferred_roles else target_role
    skills_str = ", ".join(skills[:8])

    prompt = f"""You are India's premier Placement Strategist and Tech Career Coach.
Create an executive-level, highly personalized placement roadmap and career strategy for this student:

CANDIDATE PROFILE:
- Name: {candidate_name} ({branch}, {college})
- Target / Preferred Role: {target_role} (All preferences: {roles_str})
- Preferred Target Companies: {companies_str}
- Current Skill Set: {skills_str}
- Experience Level: {exp_level}
- Target Locations: {', '.join(locations)}
- Salary Expectation: {salary_exp}

INSTRUCTIONS:
1. Focus specifically on how this candidate can crack {target_role} hiring bars at {companies_str}.
2. Provide concrete, prioritized skill gaps needed for {target_role} at {target_companies[0] if target_companies else 'top companies'}.
3. Create 4 progressive quarterly milestones (Q1 through Q4) with realistic titles and descriptions.
4. Give 3-4 specific, actionable learning recommendations (mention exact books, tools, or project architectures).
5. Provide market demand insights for 4-5 skills directly related to {target_role}.
6. Project an achievable compensation range in LPA (min and max integers).

Return ONLY valid JSON matching this schema:
{{
  "focusRecommendation": "2-3 sentences of strategic, high-impact focus advice tailored specifically for {target_role} at {companies_str}.",
  "placementProbability": 82,
  "targetCompanies": {json.dumps(target_companies)},
  "milestones": [
    {{"id": "m1", "title": "Milestone 1 Title", "description": "Specific action item for Q1", "quarter": "Q1", "status": "in_progress"}},
    {{"id": "m2", "title": "Milestone 2 Title", "description": "Specific action item for Q2", "quarter": "Q2", "status": "upcoming"}},
    {{"id": "m3", "title": "Milestone 3 Title", "description": "Specific action item for Q3", "quarter": "Q3", "status": "upcoming"}},
    {{"id": "m4", "title": "Milestone 4 Title", "description": "Specific action item for Q4", "quarter": "Q4", "status": "upcoming"}}
  ],
  "skillGaps": [
    {{"skill": "Critical Skill 1 for {target_role}", "priority": "critical", "marketDemand": 94}},
    {{"skill": "Critical Skill 2 for {target_role}", "priority": "critical", "marketDemand": 88}},
    {{"skill": "Nice to Have Skill for {target_role}", "priority": "nice_to_have", "marketDemand": 76}}
  ],
  "learningRecommendations": [
    "Read 'Designing Data-Intensive Applications' by Martin Kleppmann and build a distributed key-value store.",
    "Master advanced concurrency patterns and system design for {companies_str}.",
    "Solve 100+ LeetCode Medium/Hard problems focusing on Graphs, Dynamic Programming, and Trees.",
    "Build a production-ready portfolio project demonstrating high availability and low latency."
  ],
  "marketInsights": [
    {{"skill": "Core {target_role} Skill 1", "demand": 95, "growth": 25}},
    {{"skill": "Core {target_role} Skill 2", "demand": 90, "growth": 20}},
    {{"skill": "Cloud / DevOps Tooling", "demand": 85, "growth": 35}},
    {{"skill": "System Architecture", "demand": 88, "growth": 18}}
  ],
  "packageProjection": {{"min": 14, "max": 28}}
}}"""

    lower_role = target_role.lower()
    if "data" in lower_role or "ml" in lower_role or "ai" in lower_role or "learning" in lower_role:
        default_skill_gaps = [
            {"skill": "PyTorch / Deep Learning Architecture", "priority": "critical", "marketDemand": 95},
            {"skill": "MLOps & Model Deployment (AWS/GCP)", "priority": "critical", "marketDemand": 90},
            {"skill": "Distributed Data Pipelines (Spark/Kafka)", "priority": "nice_to_have", "marketDemand": 82},
        ]
        default_milestones = [
            {"id": "m1", "title": f"Foundations for {target_role}", "description": f"Master Deep Learning architectures & PyTorch implementations targeting {companies_str}.", "quarter": "Q1", "status": "in_progress"},
            {"id": "m2", "title": "End-to-End ML Pipeline Project", "description": "Deploy production ML model on AWS with automated CI/CD and inference monitoring.", "quarter": "Q2", "status": "upcoming"},
            {"id": "m3", "title": f"Interview Sprints for {target_companies[0]}", "description": "Targeted technical rounds on ML system design, feature engineering, and statistical modeling.", "quarter": "Q3", "status": "upcoming"},
            {"id": "m4", "title": "Offer Negotiation & Placement", "description": f"Evaluate competitive offers across {companies_str} and finalize placement.", "quarter": "Q4", "status": "upcoming"},
        ]
        default_learning = [
            "Complete fast.ai Practical Deep Learning and Hugging Face NLP specialization.",
            "Read 'Designing Machine Learning Systems' by Chip Huyen.",
            f"Implement 2 production-grade ML systems tailored to {companies_str} domain challenges.",
            "Practice ML system design mock interviews with focus on latency, throughput, and embeddings."
        ]
        default_insights = [
            {"skill": "PyTorch & Transformers", "demand": 96, "growth": 40},
            {"skill": "Vector DBs & LLM Ops", "demand": 92, "growth": 55},
            {"skill": "Data Engineering (Spark)", "demand": 86, "growth": 22},
            {"skill": "Python Performance Tuning", "demand": 84, "growth": 15},
        ]
        default_package = {"min": 16, "max": 32}
    elif "frontend" in lower_role or "ui" in lower_role or "web" in lower_role:
        default_skill_gaps = [
            {"skill": "Next.js 15 & React Server Components", "priority": "critical", "marketDemand": 94},
            {"skill": "Web Performance & Core Web Vitals", "priority": "critical", "marketDemand": 88},
            {"skill": "State Machines & Microfrontends", "priority": "nice_to_have", "marketDemand": 78},
        ]
        default_milestones = [
            {"id": "m1", "title": f"Frontend Architecture Mastery", "description": f"Build high-performance React/Next.js applications targeting {companies_str}.", "quarter": "Q1", "status": "in_progress"},
            {"id": "m2", "title": "UI Component Library & Tests", "description": "Design an accessible, WCAG-compliant design system with Cypress & Vitest suites.", "quarter": "Q2", "status": "upcoming"},
            {"id": "m3", "title": f"Frontend System Design Sprints", "description": f"Master large-scale frontend architecture for {companies_str} interview loops.", "quarter": "Q3", "status": "upcoming"},
            {"id": "m4", "title": "Placement Rounds & Conversions", "description": f"Complete hiring rounds at {companies_str} and secure top frontend engineering offers.", "quarter": "Q4", "status": "upcoming"},
        ]
        default_learning = [
            "Master React 19 concurrent features, streaming SSR, and Server Actions.",
            "Study frontend performance optimization (Lighthouse, Bundle splitting, Memoization).",
            "Read 'Frontend Architecture for Design Systems' and build an open-source UI kit.",
            "Practice live coding UI challenges and JavaScript deep-dives (Closures, Event Loop, DOM)."
        ]
        default_insights = [
            {"skill": "React / Next.js", "demand": 95, "growth": 25},
            {"skill": "TypeScript Architecture", "demand": 93, "growth": 30},
            {"skill": "Web Performance Optimization", "demand": 87, "growth": 35},
            {"skill": "State Management (Zustand/Redux)", "demand": 82, "growth": 12},
        ]
        default_package = {"min": 12, "max": 24}
    else:
        # Backend / Fullstack / Software Engineering
        default_skill_gaps = [
            {"skill": f"Distributed Systems & Concurrency", "priority": "critical", "marketDemand": 96},
            {"skill": "Database Optimization & Sharding", "priority": "critical", "marketDemand": 90},
            {"skill": "Microservices & Message Queues (Kafka/RabbitMQ)", "priority": "nice_to_have", "marketDemand": 85},
        ]
        default_milestones = [
            {"id": "m1", "title": f"Core Engineering & DS/Algo", "description": f"Solve high-frequency coding problems and master concurrency tailored for {companies_str}.", "quarter": "Q1", "status": "in_progress"},
            {"id": "m2", "title": "Scalable System Implementation", "description": f"Build an asynchronous, high-throughput microservices architecture relevant to {target_role}.", "quarter": "Q2", "status": "upcoming"},
            {"id": "m3", "title": f"System Design & Mock Loops", "description": f"Targeted system design and behavioral rounds simulating {companies_str} hiring standards.", "quarter": "Q3", "status": "upcoming"},
            {"id": "m4", "title": "Placement & Package Maximization", "description": f"Convert on-campus and off-campus applications across {companies_str}.", "quarter": "Q4", "status": "upcoming"},
        ]
        default_learning = [
            "Read 'Designing Data-Intensive Applications' by Martin Kleppmann.",
            f"Solve 150+ LeetCode Medium/Hard problems across Top {companies_str} company tags.",
            "Build a distributed rate limiter, cache, and message queue system from scratch.",
            "Practice System Design interviews with focus on CAP theorem, sharding, and caching strategies."
        ]
        default_insights = [
            {"skill": f"{target_role} Core Architecture", "demand": 95, "growth": 28},
            {"skill": "Distributed Systems & Cloud", "demand": 92, "growth": 32},
            {"skill": "Data Structures & Algorithms", "demand": 90, "growth": 15},
            {"skill": "Database Sharding & Caching", "demand": 86, "growth": 20},
        ]
        default_package = {"min": 14, "max": 28}

    default_strategy = {
        "focusRecommendation": f"Accelerate your preparation for {target_role} roles by mastering distributed system design and targeted problem solving for {companies_str}. Highlight your core technical strengths in your portfolio and resume to match their specific engineering standards.",
        "placementProbability": 84,
        "targetCompanies": target_companies,
        "milestones": default_milestones,
        "skillGaps": default_skill_gaps,
        "learningRecommendations": default_learning,
        "marketInsights": default_insights,
        "packageProjection": default_package,
    }

    strategy = call_gemini_json(prompt, default_strategy, temperature=0.3)
    if not isinstance(strategy, dict):
        strategy = default_strategy
    
    strategy.setdefault("focusRecommendation", default_strategy["focusRecommendation"])
    strategy.setdefault("placementProbability", default_strategy["placementProbability"])
    strategy.setdefault("targetCompanies", default_strategy["targetCompanies"])
    strategy.setdefault("milestones", default_strategy["milestones"])
    strategy.setdefault("skillGaps", default_strategy["skillGaps"])
    strategy.setdefault("learningRecommendations", default_strategy["learningRecommendations"])
    strategy.setdefault("marketInsights", default_strategy["marketInsights"])
    strategy.setdefault("packageProjection", default_strategy["packageProjection"])
    
    if student_id:
        try:
            supabase_client.save_career_strategy(student_id, strategy)
        except Exception as e:
            logger.error(f"Error saving generated career strategy for {student_id}: {e}")

    return strategy


def _career_payload(student_id: Optional[str], client) -> dict:
    context = _student_context(client, student_id) if student_id else {}
    strategy = supabase_client.get_career_strategy(student_id) if student_id else None
    
    career_goals = context.get("career_goals") or (context.get("student") or {}).get("career_goals") or {}
    preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
    target_role = preferred_roles[0] if preferred_roles else "Software Engineer"
    target_companies = career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
    
    # If no saved strategy or if strategy doesn't have milestones/skills, generate on the fly
    if not strategy or not (strategy.get("milestones") or strategy.get("learning_recommendations")):
        strategy = _generate_personalized_career_strategy(student_id, context)

    target_companies_list = (strategy or {}).get("target_companies") or target_companies or []
    if isinstance(target_companies_list, str):
        target_companies_list = [target_companies_list]
    
    focus = (strategy or {}).get("focus_recommendation") or (strategy or {}).get("focusRecommendation") or ""
    probability = float((strategy or {}).get("placement_probability") or (strategy or {}).get("placementProbability") or 82)
    milestones = (strategy or {}).get("milestones") or []
    skill_gaps = (strategy or {}).get("skill_gaps") or (strategy or {}).get("skillGaps") or []
    learning_recs = (strategy or {}).get("learning_recommendations") or (strategy or {}).get("learningRecommendations") or []
    market_insights = (strategy or {}).get("market_insights") or (strategy or {}).get("marketInsights") or []
    package_proj = (strategy or {}).get("package_projection") or (strategy or {}).get("packageProjection") or {"min": 12, "max": 24}

    return {
        "focusRecommendation": str(focus),
        "placementProbability": int(probability),
        "targetCompanies": target_companies_list[:10],
        "milestones": milestones,
        "skillGaps": skill_gaps,
        "learningRecommendations": learning_recs,
        "marketInsights": market_insights,
        "packageProjection": package_proj,
        "targetRole": target_role,
    }


def _dashboard_payload(student_id: Optional[str], client) -> dict:
    tracker = _tracker_payload(student_id, client)
    resume = _resume_payload(student_id, client)
    interview = _interview_payload(student_id, client)
    career = _career_payload(student_id, client)
    jobs = _fetch_live_jobs(_student_context(client, student_id), None)[:3]
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
async def onboarding(payload: dict, request: Request, background_tasks: BackgroundTasks):
    client = supabase_client.get_supabase_client()
    
    # Try getting existing student by token OR auth user directly
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "").strip() if "Bearer " in auth_header else None
    
    if not token:
        # Fallback for dev mode
        token = request.headers.get("x-supabase-auth")
        
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        if token == "guest_token":
            # Guest bypass
            return {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": payload.get("name", "Guest User"),
                "email": payload.get("email", "guest@example.com"),
                "college": payload.get("college", ""),
                "branch": payload.get("branch", ""),
            }

        user_res = client.auth.get_user(token)
        if not user_res or not user_res.user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = user_res.user.id
    except Exception as e:
        logger.error(f"Auth verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")

    student_data = _normalize_student_payload(payload)
    student_data["user_id"] = user_id # Link to auth.users.id

    try:
        # We conflict on user_id since it is definitively UNIQUE per auth user
        result = client.table("students").upsert(student_data, on_conflict="user_id").execute()
            
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create student")

        student_id = result.data[0].get("id")
        supabase_client.update_analysis_status(student_id, "starting", [], 0, "pending")
        
        # Trigger background analysis pipeline
        background_tasks.add_task(run_placement_analysis, student_id, student_data)
        
        return result.data[0]
    except Exception as e:
        logger.error(f"Error onboarding student: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/onboarding")
async def get_onboarding(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    if not student_id:
        raise HTTPException(status_code=404, detail="Student not found")
    student = client.table("students").select("*").eq("id", student_id).execute()
    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")
    return student.data[0]

@router.get("/dashboard")
async def get_dashboard(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    return _dashboard_payload(student_id, client)

@router.get("/status")
async def get_current_status(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    return _analysis_status_payload(student_id, client)

@router.get("/jobs")
async def get_live_jobs(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    # Load full context: career_goals from students table + skill_graph from student_profiles
    context = _student_context(client, student_id)
    logger.info(f"[GET /jobs] student_id={student_id}, career_goals keys={list((context.get('career_goals') or {}).keys())}")
    
    # Extract query params as a dict for filters
    filters = dict(request.query_params)
    
    # Pass the FULL context so _fetch_live_jobs can access career_goals AND skill_graph
    jobs = _fetch_live_jobs(context, filters)
    return jobs

@router.get("/resume")
async def get_resume(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    return _resume_payload(student_id, client)

@router.get("/interview")
async def get_interview(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    return _interview_payload(student_id, client)

@router.post("/interview/chat")
async def chat_interview(payload: ChatPayload, request: Request):
    client = supabase_client.get_supabase_client()
    student_id = payload.student_id or _current_student_id(client, request.headers)
    
    target_role = "Software Engineer"
    candidate_name = "Candidate"
    skills_str = "Python, Web Development, Problem Solving"
    
    if student_id:
        try:
            student_data = _student_context(client, student_id)
            student = student_data.get("student") or {}
            if student.get("name"):
                candidate_name = student.get("name")
            career_goals = student_data.get("career_goals") or student.get("career_goals") or {}
            preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
            if preferred_roles:
                target_role = preferred_roles[0]
            skills = student_data.get("skill_graph") or career_goals.get("skills") or []
            if isinstance(skills, dict):
                skills = list(skills.keys())
            if skills:
                skills_str = ", ".join(str(s) for s in skills[:8])
        except Exception as e:
            logger.error(f"Error fetching student context for mock interview: {e}")

    prompt = f"""You are a friendly, insightful, and supportive Senior Tech Lead conducting an interactive mock interview with {candidate_name} for a {target_role} position.
Candidate's key skills: {skills_str}

Behavior & Tone:
- Warm, chat-friendly, conversational, and natural (like a real human interviewer on Zoom/Slack).
- When the candidate answers: Give 1-2 sentences of encouraging, insightful feedback on what was good or how to make it stronger.
- Then ask ONE engaging, relevant follow-up question (mix of hands-on coding principles, system design, architectural choices, debugging scenarios, or behavioral experiences tailored for a {target_role}).
- If the candidate says hello, says they are ready, or asks for a question: Welcome them warmly and kick off with an introductory technical or project question.
- Keep each message concise (2-4 sentences max) so it feels like a fast, realistic conversation.
- Never use robotic cliches like "Could you elaborate on that" repeatedly.

Conversation history:
"""
    for msg in payload.history:
        role = "Interviewer" if msg.get("role") == "assistant" else "Candidate"
        prompt += f"{role}: {msg.get('content')}\n"
    prompt += "Interviewer:"
    
    fallback_question = f"Great to hear! To get started with your {target_role} interview, could you walk me through an interesting technical challenge you solved in a recent project?"
    reply = call_gemini_text(prompt, default=fallback_question, temperature=0.7)
    if not reply or not reply.strip():
        reply = fallback_question
    return {"reply": reply}

@router.get("/career")
async def get_career(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    return _career_payload(student_id, client)

@router.get("/tracker")
async def get_tracker(request: Request):
    client = supabase_client.get_supabase_client()
    student_id = _current_student_id(client, request.headers)
    return _tracker_payload(student_id, client)

@router.put("/tracker/{application_id}")
async def update_tracker_application(application_id: str, payload: dict, request: Request):
    client = supabase_client.get_supabase_client()
    stage = payload.get("stage") if isinstance(payload, dict) else None
    if not stage:
        raise HTTPException(status_code=400, detail="stage is required")
    student_id = _current_student_id(client, request.headers)
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
async def upload_resume(student_id: str, request: Request, file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF resume, extract text, run ATS analysis in background."""
    client = supabase_client.get_supabase_client()
    authenticated_student_id = _current_student_id(client, request.headers)
    if not authenticated_student_id or authenticated_student_id != student_id:
        raise HTTPException(status_code=401, detail="Unauthorized: student ID mismatch")

    try:
        content = await file.read()
        if fitz is None:
            raise HTTPException(status_code=500, detail="PyMuPDF (fitz) is not available on this server.")
        
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        if not text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from the PDF. Ensure it is not a scanned image-only PDF.")
        
        logger.info(f"[upload-resume] Extracted {len(text)} chars from {file.filename} for student {student_id}")
        
        # Upsert resume_text to students table
        client.table("students").upsert(
            {"id": student_id, "resume_text": text},
            on_conflict="id"
        ).execute()
        
        # For student_profiles: upsert (in case profile row doesn't exist yet)
        client.table("student_profiles").upsert(
            {"student_id": student_id},
            on_conflict="student_id"
        ).execute()
        
        logger.info(f"[upload-resume] resume_text saved for student {student_id}")

        result = client.table("students").select("*").eq("id", student_id).execute()
        student_row = result.data[0] if result.data else {"id": student_id, "resume_text": text}
        student_row["resume_text"] = text

        career_goals = student_row.get("career_goals") or {}
        preferred_roles = career_goals.get("preferred_roles") or career_goals.get("preferredRoles") or []
        target_role = preferred_roles[0] if preferred_roles else "Software Engineer"
        target_companies = career_goals.get("target_companies") or career_goals.get("targetCompanies") or []
        target_company = target_companies[0] if target_companies else "Tech Industry"

        try:
            from backend.tools.ats_tool import analyze_ats_compatibility, generate_optimized_resume
            from backend.utils.ai_utils import simple_tokens
            general_jd = f"Seeking a skilled {target_role} proficient in modern software engineering frameworks, system design, core technical stacks, and collaborative problem-solving for {target_company}."
            ats_result = analyze_ats_compatibility.invoke({
                "resume_text": text,
                "job_description": general_jd,
                "job_title": target_role,
                "company": target_company
            })
            if isinstance(ats_result, dict):
                job_terms = {term.lower() for term in simple_tokens(general_jd)[:30]}
                resume_terms = {term.lower() for term in simple_tokens(text)}
                overlap = job_terms & resume_terms
                ats_score = int(ats_result.get("ats_score") or min(100, max(45, len(overlap) * 8 + 45)))
                
                opt_text = ats_result.get("optimized_summary") or ats_result.get("optimized_resume")
                if not opt_text or len(str(opt_text)) < 50:
                    try:
                        opt_text = generate_optimized_resume.invoke({
                            "original_resume": text,
                            "job_description": general_jd,
                            "ats_analysis": ats_result
                        })
                    except Exception:
                        opt_text = text

                version = {
                    "ats_score": ats_score,
                    "missing_keywords": ats_result.get("missing_keywords") or sorted(list(job_terms - resume_terms))[:8],
                    "present_keywords": ats_result.get("present_keywords") or sorted(list(overlap))[:8],
                    "suggestions": ats_result.get("suggestions") or [
                        f"Highlight core {target_role} skills and project implementations.",
                        "Quantify impact with concrete metrics and achievements.",
                        f"Include relevant industry keywords for {target_role}."
                    ],
                    "optimized_resume_text": str(opt_text) if opt_text else text,
                    "original_resume_text": text,
                    "target_role": target_role,
                    "company": target_company
                }
                supabase_client.save_resume_version(student_id, "target_role", version)
                logger.info(f"[upload-resume] ATS analysis generated for target role: {target_role}")
        except Exception as e:
            logger.error(f"Error pre-generating ATS resume version: {e}")
        
        # Trigger the full placement analysis pipeline in the background
        if background_tasks:
            background_tasks.add_task(run_placement_analysis, student_id, student_row)
            logger.info(f"[upload-resume] Triggered background placement analysis for student {student_id}")
        else:
            asyncio.create_task(run_placement_analysis(student_id, student_row))
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")
    
    return {"filename": file.filename, "message": "Resume uploaded and ATS analysis generated for target role"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

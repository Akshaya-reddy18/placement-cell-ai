import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_resume_version
from backend.tools.ats_tool import analyze_ats_compatibility, generate_optimized_resume
from backend.utils.ai_utils import simple_tokens

logger = logging.getLogger("ats_agent")

def ats_agent(state: AgentState) -> AgentState:
    """Optimizes resume for top matched jobs using ATS analysis via Gemini."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "ats_agent", completed, 50)
    
    resume_text = state["student_data"].get("resume_text", "")
    if not resume_text:
        logger.warning(f"No resume text for student {student_id}")
        state["analysis_status"]["completed_agents"].append("ats_agent")
        return state
    
    top_jobs = state["matched_jobs"][:3] # Limit to top 3 for optimization
    
    resume_versions = []
    
    # If no matched jobs in state, generate ATS analysis against student's target role
    if not top_jobs:
        career_goals = state["student_data"].get("career_goals", {})
        preferred_roles = career_goals.get("preferred_roles", ["Software Engineer"])
        target_role = preferred_roles[0] if preferred_roles else "Software Engineer"
        target_company = (career_goals.get("target_companies") or ["Industry Standard"])[0]
        general_jd = f"Seeking a {target_role} proficient in modern software engineering, relevant frameworks, system design, and collaborative problem solving."
        try:
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
            if not ats_result.get("ats_score"):
                ats_result["ats_score"] = min(100, max(10, len(overlap) * 5 + 40))
            ats_result.setdefault("missing_keywords", sorted(list(job_terms - resume_terms))[:10])
            ats_result.setdefault("present_keywords", sorted(list(overlap))[:10])
            ats_result.setdefault("suggestions", ["Add more role-specific keywords and quantify achievements."])
            
            optimized_text = generate_optimized_resume.invoke({
                "original_resume": resume_text,
                "job_description": general_jd,
                "ats_analysis": ats_result
            })
            if not isinstance(optimized_text, str) or not optimized_text.strip():
                optimized_text = resume_text
            
            version = {
                "ats_score": ats_result.get("ats_score", 0),
                "missing_keywords": ats_result.get("missing_keywords", []),
                "present_keywords": ats_result.get("present_keywords", []),
                "suggestions": ats_result.get("suggestions", []),
                "optimized_resume_text": optimized_text,
                "original_resume_text": resume_text
            }
            save_resume_version(student_id, "general", version)
            resume_versions.append({**version, "job_title": target_role, "company": target_company})
        except Exception as e:
            logger.error(f"Error generating fallback ATS version for student {student_id}: {e}")
    else:
        for job in top_jobs:
            try:
                # 1. Analyze ATS compatibility
                ats_result = analyze_ats_compatibility.invoke({
                    "resume_text": resume_text,
                    "job_description": job["description"],
                    "job_title": job["title"],
                    "company": job["company"]
                })
                if not isinstance(ats_result, dict):
                    ats_result = {}

                job_terms = {term.lower() for term in simple_tokens(job["description"])[:30]}
                resume_terms = {term.lower() for term in simple_tokens(resume_text)}
                overlap = job_terms & resume_terms
                if not ats_result.get("ats_score"):
                    ats_result["ats_score"] = min(100, max(10, len(overlap) * 5 + 25))
                ats_result.setdefault("missing_keywords", sorted(list(job_terms - resume_terms))[:10])
                ats_result.setdefault("present_keywords", sorted(list(overlap))[:10])
                ats_result.setdefault("suggestions", ["Add more role-specific keywords and quantify achievements."])
                
                # 2. Generate optimized resume
                optimized_text = generate_optimized_resume.invoke({
                    "original_resume": resume_text,
                    "job_description": job["description"],
                    "ats_analysis": ats_result
                })
                if not isinstance(optimized_text, str) or not optimized_text.strip():
                    optimized_text = resume_text
                
                version = {
                    "ats_score": ats_result.get("ats_score", 0),
                    "missing_keywords": ats_result.get("missing_keywords", []),
                    "present_keywords": ats_result.get("present_keywords", []),
                    "suggestions": ats_result.get("suggestions", []),
                    "optimized_resume_text": optimized_text,
                    "original_resume_text": resume_text
                }
                
                save_resume_version(student_id, job["id"], version)
                resume_versions.append({**version, "job_title": job["title"], "company": job["company"]})
                
            except Exception as e:
                logger.error(f"Error in ATS agent for job {job.get('id')}: {e}")
                continue
            
    # 3. Update state
    state["resume_versions"] = resume_versions
    state["analysis_status"]["completed_agents"].append("ats_agent")
    update_analysis_status(student_id, "ats_agent", state["analysis_status"]["completed_agents"], 60)
    
    return state


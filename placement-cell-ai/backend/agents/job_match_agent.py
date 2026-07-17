import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_job, save_job_match
from backend.tools.job_scraper import scrape_jobs_serpapi
from backend.tools.semantic_search import embed_and_store_job, create_job_embedding_text, semantic_search_jobs, create_student_skills_text
from backend.utils.ai_utils import call_gemini_json, simple_tokens

logger = logging.getLogger("job_match_agent")

def job_match_agent(state: AgentState) -> AgentState:
    """Scrapes jobs, embeds them with Gemini, and scores matches."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "job_match_agent", completed, 30)
    
    # 1. Scrape jobs based on career goals and skills
    career_goals = state["student_data"].get("career_goals", {})
    preferred_roles = career_goals.get("preferred_roles", ["Software Engineer"])
    
    all_jobs = []
    for role in preferred_roles[:2]: # Limit to top 2 roles to avoid excessive scraping
        query = f"{role} jobs in India"
        jobs = scrape_jobs_serpapi.invoke(query)
        all_jobs.extend(jobs)
    
    # Deduplicate
    unique_jobs = {f"{j['title']}{j['company']}": j for j in all_jobs}.values()
    
    # 2. Save jobs and create Gemini embeddings
    saved_jobs = []
    for job in list(unique_jobs)[:15]: # Limit to 15 for dev
        saved = save_job(job)
        job_text = create_job_embedding_text(job)
        embed_and_store_job.invoke({"job_id": saved["id"], "job_text": job_text})
        saved_jobs.append(saved)
    
    # 3. Semantic search with Gemini embeddings
    skills_text = create_student_skills_text(state["skill_graph"], career_goals)
    semantic_matches = semantic_search_jobs.invoke({"student_skills_text": skills_text, "top_k": 10})
    
    scored_matches = []
    for job in semantic_matches:
        prompt = f"""Rate how well this student matches this job.
        
        STUDENT SKILLS: {json.dumps(state["skill_graph"])}
        STUDENT GOALS: {json.dumps(career_goals)}
        
        JOB: {job["title"]} at {job["company"]}
        DESCRIPTION: {job["description"][:1000]}
        
        Return ONLY valid JSON (no markdown):
        {{
          "match_percentage": 0-100,
          "eligibility_notes": "short explanation of why they qualify or what's missing",
          "priority_rank": "high/medium/low",
          "missing_skills": ["skill1", "skill2"],
          "matching_skills": ["skill1", "skill2"]
        }}"""

        student_skill_set = {skill.lower() for skill in state.get("skill_graph", {}).keys()}
        job_requirement_set = {skill.lower() for skill in job.get("requirements", [])}
        job_description_set = set(simple_tokens(job.get("description", "")))
        overlap = student_skill_set & (job_requirement_set | job_description_set)
        missing = sorted(list((job_requirement_set - student_skill_set)))[:5]
        match_percentage = min(100, max(10, len(overlap) * 18 + 20))
        default_result = {
            "match_percentage": match_percentage,
            "eligibility_notes": "Based on current profile and job requirements, this is a reasonable target role." if overlap else "This role is a stretch but still useful for skill building.",
            "priority_rank": "high" if match_percentage >= 70 else "medium" if match_percentage >= 45 else "low",
            "missing_skills": missing,
            "matching_skills": sorted(list(overlap))[:8],
        }

        result = call_gemini_json(prompt, default_result, temperature=0)
        result.setdefault("match_percentage", default_result["match_percentage"])
        result.setdefault("eligibility_notes", default_result["eligibility_notes"])
        result.setdefault("priority_rank", default_result["priority_rank"])
        result.setdefault("missing_skills", default_result["missing_skills"])
        result.setdefault("matching_skills", default_result["matching_skills"])

        match_record = {
            "student_id": student_id,
            "job_id": job["id"],
            "match_percentage": result["match_percentage"],
            "eligibility_notes": result["eligibility_notes"],
            "priority_rank": result["priority_rank"],
            "matching_skills": result["matching_skills"],
            "missing_skills": result["missing_skills"]
        }
        save_job_match(match_record)
        scored_matches.append({**job, **result})
    
    # 5. Update state
    state["matched_jobs"] = sorted(scored_matches, key=lambda x: x["match_percentage"], reverse=True)
    state["analysis_status"]["completed_agents"].append("job_match_agent")
    update_analysis_status(student_id, "job_match_agent", state["analysis_status"]["completed_agents"], 40)
    
    return state

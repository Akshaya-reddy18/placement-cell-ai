import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_skill_gap
from backend.utils.ai_utils import call_gemini_json, simple_tokens

logger = logging.getLogger("skill_gap_agent")

def skill_gap_agent(state: AgentState) -> AgentState:
    """Identifies skill gaps and generates personalized learning roadmap using Gemini."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "skill_gap_agent", completed, 65)
    
    # 1. Collect all required skills from matched jobs
    all_required_skills = set()
    for job in state["matched_jobs"][:10]:
        all_required_skills.update(job.get("requirements", []))
        all_required_skills.update(job.get("missing_skills", []))
    
    prompt = f"""You are a senior technical career coach. 
    Perform a comprehensive skill gap analysis and create a personalized learning roadmap.
    
    STUDENT CURRENT SKILLS (proficiency 1-10):
    {json.dumps(state["skill_graph"])}
    
    SKILLS REQUIRED BY TARGET JOBS:
    {list(all_required_skills)}
    
    TOP MATCHED JOBS:
    {[f"{j['title']} at {j['company']}" for j in state["matched_jobs"][:5]]}
    
    Return ONLY valid JSON (no markdown):
    {{
      "critical_missing": ["essential skills candidate doesn't have"],
      "nice_to_have": ["skills that would make them more competitive"],
      "emerging_trends": ["new techs in their field they should know"],
      "learning_roadmap": [
        {{"week": 1, "topic": "", "resources": [], "goal": ""}},
        {{"week": 2, "topic": "", "resources": [], "goal": ""}}
      ],
      "weekly_time_required": 10,
      "certifications": ["recommended certifications"],
      "quick_skill_wins": ["skills they can learn fast"],
      "summary": "overall advice summary"
    }}"""

    job_skills = []
    for job in state["matched_jobs"][:10]:
        job_skills.extend(job.get("requirements", []))
        job_skills.extend(job.get("missing_skills", []))

    required = {skill.lower() for skill in job_skills if skill}
    current = {skill.lower() for skill in state.get("skill_graph", {}).keys()}
    critical_missing = sorted(list(required - current))[:10]
    default_gap = {
        "critical_missing": critical_missing,
        "nice_to_have": sorted(list(required & current))[:10],
        "emerging_trends": ["cloud deployment", "system design", "data handling"],
        "learning_roadmap": [
            {"week": 1, "topic": "core missing skill 1", "resources": ["docs", "videos"], "goal": "close the biggest gap"},
            {"week": 2, "topic": "core missing skill 2", "resources": ["practice projects"], "goal": "build confidence"},
        ],
        "weekly_time_required": 10,
        "certifications": ["Google Career Certificates", "AWS Cloud Practitioner"],
        "quick_skill_wins": critical_missing[:3],
        "summary": "Focus on the most repeated requirements in the target jobs.",
    }

    gap_result = call_gemini_json(prompt, default_gap, temperature=0)
    gap_result.setdefault("critical_missing", default_gap["critical_missing"])
    gap_result.setdefault("nice_to_have", default_gap["nice_to_have"])
    gap_result.setdefault("learning_roadmap", default_gap["learning_roadmap"])
    gap_result.setdefault("certifications", default_gap["certifications"])

    save_skill_gap(student_id, gap_result)
    state["skill_gaps"] = gap_result
    state["analysis_status"]["completed_agents"].append("skill_gap_agent")
    update_analysis_status(student_id, "skill_gap_agent", state["analysis_status"]["completed_agents"], 75)
    return state

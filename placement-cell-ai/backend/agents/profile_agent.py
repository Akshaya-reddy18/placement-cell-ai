import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_student_profile
from backend.tools.resume_parser import parse_resume_text
from backend.tools.github_tool import analyze_github_profile
from backend.utils.ai_utils import call_gemini_json

logger = logging.getLogger("profile_agent")

def profile_agent(state: AgentState) -> AgentState:
    """Parses resume, analyzes GitHub, builds skill graph using Gemini."""
    student_id = state["student_id"]
    student_data = state["student_data"]
    
    update_analysis_status(student_id, "profile_agent", [], 10)
    
    # 1. Parse resume
    resume_text = student_data.get("resume_text", "")
    parsed_resume = {}
    if resume_text:
        parsed_resume = parse_resume_text.invoke(resume_text)
    
    # 2. Analyze GitHub
    github_username = student_data.get("github_username")
    github_result = {}
    if github_username:
        github_result = analyze_github_profile.invoke(github_username)
    
    prompt = f"""You are a professional technical career advisor. 
    Analyze the following resume and GitHub data to build a comprehensive skill graph and domain expertise profile.
    
    RESUME DATA:
    {json.dumps(parsed_resume)}
    
    GITHUB DATA:
    {json.dumps(github_result)}
    
    Return ONLY valid JSON (no markdown backticks):
    {{
      "skill_graph": {{"Python": 8, "React": 6, "SQL": 7}},
      "domain_scores": {{"backend": 8, "frontend": 5, "ml": 3, "devops": 4, "mobile": 2}},
      "profile_completeness": 0-100,
      "strength_analysis": "one paragraph analysis of candidate strengths",
      "career_profile": "one paragraph career summary"
    }}"""

    resume_skills = parsed_resume.get("skills", []) if isinstance(parsed_resume, dict) else []
    github_skills = list((github_result.get("skill_scores") or {}).keys()) if isinstance(github_result, dict) else []
    combined_skills = resume_skills + github_skills + list(state["student_data"].get("career_goals", {}).get("preferred_skills", []))
    skill_graph = {}
    for skill in combined_skills:
        normalized = str(skill).strip()
        if not normalized:
            continue
        skill_graph[normalized] = min(10, skill_graph.get(normalized, 0) + 2)

    if not skill_graph:
        skill_graph = {"Python": 6, "Problem Solving": 6, "Communication": 6}

    default_profile = {
        "skill_graph": skill_graph,
        "domain_scores": github_result.get("domain_expertise", {}) if isinstance(github_result, dict) else {},
        "profile_completeness": min(100, 40 + len(skill_graph) * 10),
        "strength_analysis": "Profile generated using resume and GitHub signals.",
        "career_profile": "Candidate profile synthesized from available resume and project evidence.",
    }

    profile_result = call_gemini_json(prompt, default_profile, temperature=0)
    if isinstance(profile_result.get("career_profile"), dict):
        profile_result["career_profile"] = profile_result["career_profile"].get("summary", "Candidate profile synthesized from available resume and project evidence.")

    save_student_profile(student_id, {
        "skill_graph": profile_result.get("skill_graph", skill_graph),
        "domain_scores": profile_result.get("domain_scores", {}),
        "strength_analysis": profile_result.get("strength_analysis", ""),
        "career_profile": {"summary": profile_result.get("career_profile", "")},
        "profile_completeness": profile_result.get("profile_completeness", 0)
    })

    state["skill_graph"] = profile_result.get("skill_graph", skill_graph)
    state["domain_scores"] = profile_result.get("domain_scores", {})
    state["student_data"]["parsed_resume"] = parsed_resume
    state["student_data"]["github_result"] = github_result
    state["analysis_status"]["completed_agents"].append("profile_agent")
    return state

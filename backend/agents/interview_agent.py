import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_interview_session
from backend.tools.interview_tool import generate_interview_questions
from backend.utils.ai_utils import call_gemini_json

logger = logging.getLogger("interview_agent")

def interview_agent(state: AgentState) -> AgentState:
    """Generates interview prep material and readiness scores using Gemini."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "interview_agent", completed, 75)
    
    top_job = state["matched_jobs"][0] if state["matched_jobs"] else {}
    job_desc = top_job.get("description", "Software Engineer position")
    
    # 1. Generate question bank
    questions_bank = {}
    for q_type in ["hr", "technical", "system_design", "project"]:
        questions = generate_interview_questions.invoke({
            "student_profile": {
                "skills": state["skill_graph"],
                "projects": state["student_data"].get("parsed_resume", {}).get("projects", [])
            },
            "job_description": job_desc,
            "question_type": q_type,
            "num_questions": 3
        })
        questions_bank[q_type] = questions
    
    prompt = f"""Based on this student profile and identified gaps, estimate interview readiness.
    
    SKILL GRAPH: {json.dumps(state["skill_graph"])}
    SKILL GAPS: {json.dumps(state.get("skill_gaps", {}).get("critical_missing", []))}
    DOMAIN SCORES: {json.dumps(state.get("domain_scores", {}))}
    
    Return ONLY valid JSON (no markdown):
    {{
      "readiness_score": 0-100,
      "confidence_score": 0-100,
      "weak_areas": ["specific topics"],
      "strong_areas": ["specific topics"],
      "preparation_priority": ["what to study first"]
    }}"""

    skill_score = sum(state.get("skill_graph", {}).values()) / len(state.get("skill_graph", {})) if state.get("skill_graph") else 0
    gap_count = len(state.get("skill_gaps", {}).get("critical_missing", []))
    default_readiness = {
        "readiness_score": max(0, min(100, round(skill_score * 8 + len(state.get("matched_jobs", [])) * 6 - gap_count * 4))),
        "confidence_score": max(0, min(100, round(55 + len(questions_bank) * 5 - gap_count * 2))),
        "weak_areas": state.get("skill_gaps", {}).get("critical_missing", [])[:5],
        "strong_areas": sorted(state.get("skill_graph", {}).keys(), key=lambda skill: state["skill_graph"][skill], reverse=True)[:5],
        "preparation_priority": ["Revise weak technical concepts", "Practice project explanations", "Prepare behavioral answers"],
    }

    readiness = call_gemini_json(prompt, default_readiness, temperature=0)
    readiness.setdefault("readiness_score", default_readiness["readiness_score"])
    readiness.setdefault("confidence_score", default_readiness["confidence_score"])
    readiness.setdefault("weak_areas", default_readiness["weak_areas"])
    readiness.setdefault("strong_areas", default_readiness["strong_areas"])
    readiness.setdefault("preparation_priority", default_readiness["preparation_priority"])

    session_data = {
        "session_type": "prep",
        "questions_bank": questions_bank,
        "readiness_score": readiness["readiness_score"],
        "confidence_score": readiness["confidence_score"],
        "weak_areas": readiness["weak_areas"],
        "strong_areas": readiness["strong_areas"]
    }
    save_interview_session(student_id, session_data)

    state["interview_prep"] = session_data
    state["analysis_status"]["completed_agents"].append("interview_agent")
    update_analysis_status(student_id, "interview_agent", state["analysis_status"]["completed_agents"], 85)
    return state

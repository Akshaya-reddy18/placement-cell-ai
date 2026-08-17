import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, mark_analysis_complete
from backend.utils.ai_utils import call_gemini_json

logger = logging.getLogger("tracking_agent")

def tracking_agent(state: AgentState) -> AgentState:
    """Aggregates all data into a tracking dashboard. Final graph node."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "tracking_agent", completed, 95)
    
    # 1. Generate next actions using Gemini
    prompt = f"""Based on this student's analysis, list the top 5 priority actions for THIS WEEK.
    
    CONTEXT:
    Skill Gaps: {json.dumps(state.get("skill_gaps", {}).get("critical_missing", []))}
    Interview Readiness: {state.get("interview_prep", {}).get("readiness_score", 0)}%
    Career Strategy: {json.dumps(state.get("career_strategy", {}).get("focus_recommendation"))}
    
    Return ONLY a valid JSON array:
    [
      {{"action": "string", "priority": "high/medium", "why": "string", "time_needed": "hours"}}
    ]"""

    default_actions = [
        {"action": "Improve the resume for the top target role", "priority": "high", "why": "This improves match and ATS scores immediately.", "time_needed": 3},
        {"action": "Study the top 3 missing skills", "priority": "high", "why": "These are the most repeated requirements in target jobs.", "time_needed": 6},
        {"action": "Practice interview answers", "priority": "medium", "why": "Readiness improves with repetition.", "time_needed": 4},
        {"action": "Apply to 10 relevant jobs", "priority": "medium", "why": "The pipeline needs active applications to convert into interviews.", "time_needed": 2},
        {"action": "Reach out for referrals", "priority": "medium", "why": "Warm intros improve recruiter response rates.", "time_needed": 2},
    ]

    next_actions = call_gemini_json(prompt, default_actions, temperature=0)
    if not isinstance(next_actions, list):
        next_actions = default_actions
    state["messages"].append({"role": "assistant", "content": "Analysis complete. Check your dashboard for the roadmap."})
    state["analysis_status"]["next_actions"] = next_actions
    
    # Finalize
    state["analysis_status"]["completed_agents"].append("tracking_agent")
    mark_analysis_complete(student_id, state["analysis_status"]["completed_agents"])
    
    return state

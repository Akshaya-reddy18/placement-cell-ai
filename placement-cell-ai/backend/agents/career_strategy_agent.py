import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_career_strategy
from backend.utils.ai_utils import call_gemini_json

logger = logging.getLogger("career_strategy_agent")

def career_strategy_agent(state: AgentState) -> AgentState:
    """Synthesizes all data using Gemini to create a comprehensive placement strategy."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "career_strategy_agent", completed, 90)
    
    prompt = f"""You are India's top placement advisor with 15 years of experience.
    Create a comprehensive, honest, and actionable placement strategy for this student.
    
    CONTEXT:
    Skill Graph: {json.dumps(state["skill_graph"])}
    Domain Scores: {json.dumps(state["domain_scores"])}
    Skill Gaps: {json.dumps(state.get("skill_gaps", {}).get("critical_missing", []))}
    Interview Readiness: {state.get("interview_prep", {}).get("readiness_score", 0)}%
    Matched Jobs: {[f"{j['title']} at {j['company']}" for j in state["matched_jobs"][:5]]}
    
    Return ONLY valid JSON (no markdown):
    {{
      "target_companies": ["list of 10 ideal companies"],
      "focus_recommendation": {{"primary_focus": "string", "why": "string"}},
      "skill_roi": ["skills with highest job return"],
      "placement_probability": 0-100,
      "action_plan_90_days": ["milestones for 30, 60, 90 days"],
      "red_flags": ["concerning areas"],
      "quick_wins": ["fast improvements"],
      "honest_assessment": "one paragraph direct advice",
      "predicted_package_range": {{"min": "LPA", "max": "LPA"}}
    }}"""

    default_strategy = {
        "target_companies": [job["company"] for job in state["matched_jobs"][:10]],
        "focus_recommendation": {"primary_focus": "Strengthen the highest-paying target role fit", "why": "It matches current skills and job demand."},
        "skill_roi": sorted(state.get("skill_graph", {}).keys())[:8],
        "placement_probability": min(100, max(0, state.get("interview_prep", {}).get("readiness_score", 0))),
        "action_plan_90_days": ["Days 1-30: close key skill gaps", "Days 31-60: optimize resume and apply", "Days 61-90: intensify interview practice"],
        "red_flags": ["Sparse project evidence" if len(state.get("skill_graph", {})) < 5 else ""],
        "quick_wins": ["Update resume keywords", "Practice 5 interview questions", "Apply to 10 target jobs"],
        "honest_assessment": "You can become interview-ready, but you need disciplined execution over the next 90 days.",
        "predicted_package_range": {"min": "4", "max": "10"},
    }

    strategy = call_gemini_json(prompt, default_strategy, temperature=0)
    strategy.setdefault("target_companies", default_strategy["target_companies"])
    strategy.setdefault("focus_recommendation", default_strategy["focus_recommendation"])
    strategy.setdefault("skill_roi", default_strategy["skill_roi"])
    strategy.setdefault("placement_probability", default_strategy["placement_probability"])
    strategy.setdefault("action_plan_90_days", default_strategy["action_plan_90_days"])
    strategy.setdefault("quick_wins", default_strategy["quick_wins"])
    save_career_strategy(student_id, strategy)

    state["career_strategy"] = strategy
    state["analysis_status"]["completed_agents"].append("career_strategy_agent")
    update_analysis_status(student_id, "career_strategy_agent", state["analysis_status"]["completed_agents"], 95)
    return state

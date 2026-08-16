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
    Student Constraints: {json.dumps(state["student_data"].get("career_goals", {}))}
    
    Return ONLY valid JSON (no markdown) with this exact schema:
    {{
      "focusRecommendation": "string",
      "placementProbability": 0-100,
      "targetCompanies": ["company1", "company2"],
      "milestones": [
        {{"id": "string", "title": "string", "description": "string", "quarter": "string", "status": "upcoming"}}
      ],
      "skillGaps": [
        {{"skill": "string", "priority": "critical" | "nice_to_have", "marketDemand": 0-100}}
      ],
      "learningRecommendations": ["course or topic 1"],
      "marketInsights": [
        {{"skill": "string", "demand": 0-100, "growth": 0-100}}
      ],
      "packageProjection": {{"min": 0, "max": 0}}
    }}"""

    default_strategy = {
      "focusRecommendation": "Strengthen backend skills and prepare for technical interviews",
      "placementProbability": min(100, max(10, state.get("interview_prep", {}).get("readiness_score", 0))),
      "targetCompanies": [job["company"] for job in state["matched_jobs"][:5]],
      "milestones": [
        {"id": "m1", "title": "Close Skill Gaps", "description": "Complete advanced React tutorial", "quarter": "Q1", "status": "in_progress"},
        {"id": "m2", "title": "Resume Polish", "description": "Update resume with new projects", "quarter": "Q1", "status": "upcoming"}
      ],
      "skillGaps": [{"skill": "System Design", "priority": "critical", "marketDemand": 90}],
      "learningRecommendations": ["Read Designing Data-Intensive Applications", "Leetcode Mediums"],
      "marketInsights": [{"skill": "React", "demand": 95, "growth": 20}],
      "packageProjection": {"min": 5, "max": 12}
    }

    strategy = call_gemini_json(prompt, default_strategy, temperature=0)
    strategy.setdefault("focusRecommendation", default_strategy["focusRecommendation"])
    strategy.setdefault("placementProbability", default_strategy["placementProbability"])
    strategy.setdefault("targetCompanies", default_strategy["targetCompanies"])
    strategy.setdefault("milestones", default_strategy["milestones"])
    strategy.setdefault("skillGaps", default_strategy["skillGaps"])
    strategy.setdefault("learningRecommendations", default_strategy["learningRecommendations"])
    strategy.setdefault("marketInsights", default_strategy["marketInsights"])
    strategy.setdefault("packageProjection", default_strategy["packageProjection"])
    save_career_strategy(student_id, strategy)

    state["career_strategy"] = strategy
    state["analysis_status"]["completed_agents"].append("career_strategy_agent")
    update_analysis_status(student_id, "career_strategy_agent", state["analysis_status"]["completed_agents"], 95)
    return state

import logging

from backend.schemas.state import AgentState

logger = logging.getLogger("probability_predictor")


def probability_predictor(state: AgentState) -> AgentState:
	"""Estimate placement probability from skills, matches, ATS, and interview readiness."""
	skill_graph = state.get("skill_graph", {})
	matched_jobs = state.get("matched_jobs", [])
	resume_versions = state.get("resume_versions", [])
	skill_gaps = state.get("skill_gaps", {}).get("critical_missing", [])
	interview_readiness = state.get("interview_prep", {}).get("readiness_score", 0)

	avg_skill = sum(skill_graph.values()) / len(skill_graph) if skill_graph else 0
	best_match = max((job.get("match_percentage", 0) for job in matched_jobs), default=0)
	best_ats = max((version.get("ats_score", 0) for version in resume_versions), default=0)

	probability = (
		avg_skill * 5
		+ best_match * 0.25
		+ best_ats * 0.2
		+ interview_readiness * 0.3
		- len(skill_gaps) * 3
	)
	probability = max(0, min(100, round(probability)))

	explanation = {
		"placement_probability": probability,
		"drivers": {
			"skill_strength": round(avg_skill, 1),
			"top_job_match": round(best_match, 1),
			"ats_compatibility": round(best_ats, 1),
			"interview_readiness": round(interview_readiness, 1),
			"critical_gaps": len(skill_gaps),
		},
		"assessment": "Strong" if probability >= 70 else "Moderate" if probability >= 45 else "Needs improvement",
		"advice": [
			"Improve the weakest technical areas first.",
			"Tailor the resume for top target roles.",
			"Practice interviews weekly and track progress.",
		],
	}

	state["placement_probability"] = explanation
	state.setdefault("messages", []).append({
		"role": "assistant",
		"content": f"Placement probability estimated at {probability}%.",
	})
	logger.info("Probability prediction completed for student %s", state.get("student_id"))
	return state

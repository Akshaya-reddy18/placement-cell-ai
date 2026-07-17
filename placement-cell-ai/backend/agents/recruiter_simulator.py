import logging

from backend.schemas.state import AgentState

logger = logging.getLogger("recruiter_simulator")


def recruiter_simulator(state: AgentState) -> AgentState:
	"""Simulate a recruiter-style review of the candidate profile."""
	matched_jobs = state.get("matched_jobs", [])[:3]
	skill_graph = state.get("skill_graph", {})
	interview_readiness = state.get("interview_prep", {}).get("readiness_score", 0)

	strengths = sorted(skill_graph.items(), key=lambda item: item[1], reverse=True)[:5]
	concerns = []
	if not matched_jobs:
		concerns.append("No target jobs were identified yet.")
	if interview_readiness < 50:
		concerns.append("Interview readiness is below target for most screening rounds.")
	if len(skill_graph) < 5:
		concerns.append("Profile signals are still too thin for a confident hiring decision.")

	likely_decision = "advance" if interview_readiness >= 65 and len(matched_jobs) >= 1 else "hold"
	review = {
		"likely_decision": likely_decision,
		"strengths": [f"{skill}: {score}/10" for skill, score in strengths],
		"concerns": concerns,
		"likely_questions": [
			f"Explain your experience with {skill}." for skill, _ in strengths[:3]
		] or ["Walk me through your strongest project."],
		"next_steps": [
			"Refine resume to align with target roles.",
			"Practice technical and behavioral interview answers.",
			"Apply to roles that match the current skill profile.",
		],
	}

	state["recruiter_simulation"] = review
	state.setdefault("messages", []).append({
		"role": "assistant",
		"content": f"Recruiter simulation complete: {likely_decision}."
	})
	logger.info("Recruiter simulation completed for student %s", state.get("student_id"))
	return state

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
import logging

from backend.agents.profile_agent import profile_agent
from backend.agents.job_match_agent import job_match_agent
from backend.agents.ats_agent import ats_agent
from backend.agents.skill_gap_agent import skill_gap_agent
from backend.agents.interview_agent import interview_agent
from backend.agents.referral_agent import referral_agent
from backend.agents.career_strategy_agent import career_strategy_agent
from backend.agents.tracking_agent import tracking_agent
from backend.schemas.state import AgentState

# Configure logging
logger = logging.getLogger("placement_graph")

def check_profile_complete(state: AgentState) -> str:
    """Conditional edge to check if profile analysis was successful."""
    if state.get("error") or not state.get("skill_graph"):
        logger.error(f"Profile analysis failed for student {state.get('student_id')}: {state.get('error')}")
        return "error_handler"
    return "job_match_agent"

def error_handler(state: AgentState) -> AgentState:
    """Gracefully handle errors in the graph."""
    logger.error(f"Graph execution error for student {state.get('student_id')}: {state.get('error')}")
    # You might want to update the status in DB here as well
    return state

def create_placement_graph():
    """Builds and compiles the LangGraph StateGraph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("profile_agent", profile_agent)
    workflow.add_node("job_match_agent", job_match_agent)
    workflow.add_node("ats_agent", ats_agent)
    workflow.add_node("skill_gap_agent", skill_gap_agent)
    workflow.add_node("interview_agent", interview_agent)
    workflow.add_node("referral_agent", referral_agent)
    workflow.add_node("career_strategy_agent", career_strategy_agent)
    workflow.add_node("tracking_agent", tracking_agent)
    workflow.add_node("error_handler", error_handler)
    
    # Define edges
    workflow.add_edge(START, "profile_agent")
    
    # Conditional edge after profile_agent
    workflow.add_conditional_edges(
        "profile_agent",
        check_profile_complete,
        {
            "job_match_agent": "job_match_agent",
            "error_handler": "error_handler"
        }
    )
    
    # Sequential edges for the rest of the pipeline
    workflow.add_edge("job_match_agent", "ats_agent")
    workflow.add_edge("ats_agent", "skill_gap_agent")
    workflow.add_edge("skill_gap_agent", "interview_agent")
    workflow.add_edge("interview_agent", "referral_agent")
    workflow.add_edge("referral_agent", "career_strategy_agent")
    workflow.add_edge("career_strategy_agent", "tracking_agent")
    workflow.add_edge("tracking_agent", END)
    
    # Error handler leads to END
    workflow.add_edge("error_handler", END)
    
    # Compile with MemorySaver checkpointing
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Initialize the graph
placement_graph = create_placement_graph()

async def run_placement_analysis(student_id: str, student_data: dict) -> dict:
    """Executes the full placement analysis pipeline for a student."""
    initial_state = {
        "student_id": student_id,
        "student_data": student_data,
        "skill_graph": {}, 
        "domain_scores": {}, 
        "job_listings": [], 
        "matched_jobs": [],
        "resume_versions": [], 
        "skill_gaps": {}, 
        "interview_prep": {}, 
        "referrals": [],
        "career_strategy": {}, 
        "applications": [],
        "analysis_status": {
            "current_agent": "starting", 
            "completed_agents": [], 
            "percentage": 0,
            "status": "running"
        },
        "error": None, 
        "messages": []
    }
    
    config = {"configurable": {"thread_id": student_id}}
    
    try:
        final_state = await placement_graph.ainvoke(initial_state, config)
        return {"success": True, "state": final_state}
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {str(e)}")
        from backend.db.supabase_client import mark_analysis_failed
        mark_analysis_failed(student_id, str(e))
        return {"success": False, "error": str(e)}

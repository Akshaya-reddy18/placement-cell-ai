import os
import json
import logging
from backend.schemas.state import AgentState
from backend.db.supabase_client import update_analysis_status, save_referral
from backend.utils.ai_utils import call_gemini_json

logger = logging.getLogger("referral_agent")

def referral_agent(state: AgentState) -> AgentState:
    """Generates personalized referral strategies using Gemini."""
    student_id = state["student_id"]
    completed = state["analysis_status"]["completed_agents"]
    update_analysis_status(student_id, "referral_agent", completed, 85)
    
    top_companies = [job["company"] for job in state["matched_jobs"][:5]]
    referrals = []
    
    for company in set(top_companies):
        matching_job = next((j for j in state["matched_jobs"] if j["company"] == company), {})
        
        prompt = f"""Generate a referral networking strategy for this student targeting {company}.
        
        STUDENT PROFILE:
        Skills: {list(state["skill_graph"].keys())[:10]}
        Target Role: {matching_job.get("title", "Software Engineer")}
        
        COMPANY: {company}
        
        Return ONLY valid JSON (no markdown):
        {{
          "company": "{company}",
          "target_role": "{matching_job.get("title", "Software Engineer")}",
          "connection_types": ["alumni", "recruiter", "engineer"],
          "outreach_templates": {{
            "linkedin_invite": "text",
            "cold_email": "text"
          }},
          "referral_pathway": ["step 1", "step 2"],
          "where_to_find_contacts": ["specific groups or platforms"],
          "dos_and_donts": {{"dos": [], "donts": []}}
        }}"""
        
        default_result = {
            "company": company,
            "target_role": matching_job.get("title", "Software Engineer"),
            "connection_types": ["alumni", "recruiter", "engineer"],
            "outreach_templates": {
                "linkedin_invite": f"Hi, I’m exploring {matching_job.get('title', 'tech roles')} at {company} and would love to connect.",
                "cold_email": f"Hello, I’m a student preparing for {matching_job.get('title', 'tech roles')} roles and would appreciate any advice about {company}."
            },
            "referral_pathway": ["Find alumni", "Send concise outreach", "Follow up after 5 days"],
            "where_to_find_contacts": ["LinkedIn", "alumni groups", "college network"],
            "dos_and_donts": {"dos": ["Be brief", "Show relevance"], "donts": ["Ask for a job immediately", "Use generic templates"]}
        }

        result = call_gemini_json(prompt, default_result, temperature=0.3)
        result.setdefault("company", company)
        result.setdefault("target_role", matching_job.get("title", "Software Engineer"))
        result.setdefault("connection_types", ["alumni", "recruiter", "engineer"])
        result.setdefault("outreach_templates", default_result["outreach_templates"])
        result.setdefault("referral_pathway", default_result["referral_pathway"])
        result.setdefault("where_to_find_contacts", default_result["where_to_find_contacts"])
        result.setdefault("dos_and_donts", default_result["dos_and_donts"])
        save_referral(student_id, result)
        referrals.append(result)
            
    # Update state
    state["referrals"] = referrals
    state["analysis_status"]["completed_agents"].append("referral_agent")
    update_analysis_status(student_id, "referral_agent", state["analysis_status"]["completed_agents"], 90)
    
    return state

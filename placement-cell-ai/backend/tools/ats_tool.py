import os
import json
import logging
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("ats_tool")

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0
    )

@tool
def analyze_ats_compatibility(resume_text: str, job_description: str, job_title: str = "", company: str = "") -> dict:
    """Analyze resume against a job description for ATS compatibility and suggest optimizations."""
    llm = get_llm()
    if llm is None:
        return {
            "ats_score": 50,
            "keyword_match_rate": 50,
            "missing_keywords": [],
            "present_keywords": [],
            "suggestions": ["Add more role-specific keywords and quantify achievements."],
            "optimized_summary": "Local fallback ATS summary.",
            "section_scores": {"skills": 50, "experience": 50, "education": 50, "projects": 50},
            "formatting_issues": [],
            "optimized_skills_section": "Local fallback skills section.",
        }
    
    prompt = f"""You are an expert ATS analyst with deep knowledge of how recruiting software screens resumes.
    You know the exact keyword matching algorithms used by Workday, Greenhouse, Lever, and Taleo.
    
    Analyze this resume against the job description for ATS compatibility.
    Return ONLY valid JSON (no markdown backticks, no preamble):
    
    JOB TITLE: {job_title} at {company}
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME:
    {resume_text}
    
    {{
      "ats_score": 0,
      "keyword_match_rate": 0,
      "missing_keywords": ["critical keywords from JD missing in resume"],
      "present_keywords": ["JD keywords already in resume"],
      "suggestions": ["specific actionable changes"],
      "optimized_summary": "rewrite resume summary for this JD",
      "section_scores": {{
        "skills": 0,
        "experience": 0,
        "education": 0,
        "projects": 0
      }},
      "formatting_issues": ["any formatting problems that hurt ATS"],
      "optimized_skills_section": "rewritten skills section with missing keywords added"
    }}"""
    
    try:
        response = llm.invoke(prompt)
        clean_text = response.content.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:]
        clean_text = clean_text.strip()
        
        return json.loads(clean_text)
    except Exception as e:
        logger.error(f"Error in ATS analysis: {e}")
        return {"ats_score": 0, "error": str(e)}

@tool
def generate_optimized_resume(original_resume: str, job_description: str, ats_analysis: dict) -> str:
    """Generate a fully optimized resume version for a specific job using Gemini."""
    llm = get_llm()
    
    prompt = f"""You are a professional resume writer. Rewrite the following resume to be highly optimized for the provided job description and ATS analysis.
    
    - Integrate missing keywords naturally.
    - Use quantified achievements (e.g., "Increased X by Y%").
    - Highlight job-relevant skills.
    - Keep it clean and professional markdown format.
    
    ORIGINAL RESUME:
    {original_resume}
    
    JOB DESCRIPTION:
    {job_description}
    
    ATS ANALYSIS:
    {json.dumps(ats_analysis)}
    
    Return the optimized resume as clean markdown text only."""
    
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error generating optimized resume: {e}")
        return original_resume

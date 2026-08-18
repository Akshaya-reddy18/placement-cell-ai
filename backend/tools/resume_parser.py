try:
    import fitz  # PyMuPDF
except ImportError as e:
    fitz = None
    import logging
    logging.getLogger("resume_parser").warning(f"Failed to import fitz: {e}")
import os
import json
import logging
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger("resume_parser")

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0
    )

def extract_resume_data(resume_text: str) -> dict:
    """Extract structured information from resume text using Gemini AI."""
    llm = get_llm()
    if llm is None:
        tokens = resume_text.split()
        inferred_skills = [skill for skill in ["Python", "FastAPI", "SQL", "React", "Git", "Docker"] if skill.lower() in resume_text.lower()]
        return {
            "name": tokens[0] + " " + tokens[1] if len(tokens) > 1 else "Unknown",
            "email": None,
            "phone": None,
            "location": None,
            "summary": "Resume parsed locally because Gemini is unavailable.",
            "skills": inferred_skills,
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
            "languages": [skill for skill in inferred_skills if skill in {"Python", "SQL"}],
        }
    
    prompt = f"""You are a professional resume parser. Extract information exactly as it appears. 
    Return ONLY valid JSON with no markdown, no backticks, and no preamble.
    
    Extract from this resume and return as JSON only:
    {{
      "name": "full name",
      "email": "email address",
      "phone": "phone number",
      "location": "city/state",
      "summary": "professional summary if present",
      "skills": ["list", "of", "skills"],
      "experience": [
        {{"company": "", "role": "", "duration": "", "start_date": "", "end_date": "", "description": "bullet points", "tech_used": []}}
      ],
      "education": [
        {{"institution": "", "degree": "", "field": "", "year": "", "cgpa": ""}}
      ],
      "projects": [
        {{"name": "", "description": "", "tech_stack": [], "url": "", "github": ""}}
      ],
      "certifications": [{{"name": "", "issuer": "", "year": ""}}],
      "achievements": ["list of achievements"],
      "languages": ["programming languages only"]
    }}
    
    Resume text:
    {resume_text}"""
    
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
        logger.error(f"Error extracting resume data: {e}")
        return {"error": str(e), "raw_text": resume_text[:500]}

@tool
def parse_resume_pdf(pdf_path: str) -> dict:
    """Parse a PDF resume file and extract structured information."""
    try:
        if fitz is None:
            return {"error": "PyMuPDF (fitz) is not available on this system due to an import error."}
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return extract_resume_data(text)
    except Exception as e:
        logger.error(f"Error opening PDF {pdf_path}: {e}")
        return {"error": f"Failed to open PDF: {str(e)}"}

@tool
def parse_resume_text(resume_text: str) -> dict:
    """Parse resume text and extract structured information using Gemini AI."""
    return extract_resume_data(resume_text)

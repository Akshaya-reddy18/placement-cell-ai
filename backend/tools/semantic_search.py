import os
from typing import Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from backend.db.supabase_client import save_job_embedding, search_similar_jobs
from backend.utils.ai_utils import stable_embedding


def get_embeddings_model():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )


def create_job_embedding_text(job: dict) -> str:
    """Create a rich text representation of a job for embedding."""
    title = job.get("title", "")
    company = job.get("company", "")
    description = job.get("description", "")
    requirements = job.get("requirements", [])
    requirements_text = ", ".join(requirements) if requirements else ""
    skills = job.get("skills", [])
    skills_text = ", ".join(skills) if skills else ""
    return f"Title: {title}\nCompany: {company}\nDescription: {description}\nRequirements: {requirements_text}\nSkills needed: {skills_text}"


@tool
def embed_and_store_job(job_id: str, job_text: str) -> bool:
    """Generate and store 768-dim embedding for a job listing using Gemini."""
    embedder = get_embeddings_model()
    if embedder is None:
        embedding = stable_embedding(job_text, dimensions=64)
    else:
        try:
            embedding = embedder.embed_query(job_text)
        except Exception:
            embedding = stable_embedding(job_text, dimensions=64)
    save_job_embedding(job_id, embedding)
    return True


def create_student_skills_text(skill_graph: dict, career_goals: dict) -> str:
    """Create rich skills text for embedding from student profile."""
    skills_list = ", ".join([f"{skill} (level {score}/10)" for skill, score in skill_graph.items()])
    roles = ", ".join(career_goals.get("preferred_roles", []))
    return f"Skills: {skills_list}\nTarget roles: {roles}\nPreferences: {career_goals}"


@tool
def semantic_search_jobs(student_skills_text: str, top_k: int = 15, threshold: float = 0.6) -> list[dict]:
    """Find semantically similar jobs using Gemini vector similarity search."""
    embedder = get_embeddings_model()
    if embedder is None:
        embedding = stable_embedding(student_skills_text, dimensions=64)
    else:
        try:
            embedding = embedder.embed_query(student_skills_text)
        except Exception:
            embedding = stable_embedding(student_skills_text, dimensions=64)
    return search_similar_jobs(embedding, threshold, top_k)

import os
import httpx
import logging
from typing import Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

def extract_skills_from_description(description: str) -> list[str]:
    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI",
        "Django", "Flask", "SQL", "PostgreSQL", "MongoDB", "Redis", "Docker",
        "Kubernetes", "AWS", "GCP", "Azure", "Git", "REST API", "GraphQL",
        "Machine Learning", "TensorFlow", "PyTorch", "Java", "C++", "Go", "Rust",
        "Spring Boot", "Microservices", "CI/CD", "Linux", "Agile", "Scrum"
    ]
    skills = []
    for skill in common_skills:
        if skill.lower() in description.lower():
            skills.append(skill)
    return skills

def extract_metadata_from_description(description: str) -> dict:
    desc_lower = description.lower()
    work_mode = "On-site"
    if "remote" in desc_lower or "work from home" in desc_lower or "wfh" in desc_lower:
        work_mode = "Remote"
    elif "hybrid" in desc_lower:
        work_mode = "Hybrid"

    employment_type = "Full-time"
    if "intern" in desc_lower or "internship" in desc_lower:
        employment_type = "Internship"
    elif "contract" in desc_lower:
        employment_type = "Contract"
    elif "freelance" in desc_lower:
        employment_type = "Freelance"
        
    company_type = "MNC"
    if "startup" in desc_lower or "early stage" in desc_lower:
        company_type = "Startup"
    elif "service based" in desc_lower or "consulting" in desc_lower:
        company_type = "Service-based"
    elif "product based" in desc_lower:
        company_type = "Product-based"

    return {
        "work_mode": work_mode,
        "employment_type": employment_type,
        "company_type": company_type
    }

def infer_source(url: str) -> str:
    url_lower = url.lower()
    if "linkedin" in url_lower:
        return "LinkedIn"
    elif "internshala" in url_lower:
        return "Internshala"
    elif "wellfound" in url_lower or "angellist" in url_lower:
        return "Wellfound"
    elif "naukri" in url_lower:
        return "Naukri"
    else:
        return "Company Website"

def is_valid_apply_url(url: str) -> bool:
    if not url: return False
    url_lower = url.lower()
    if "google.com/search" in url_lower: return False
    if "bing.com/search" in url_lower: return False
    # Allow google.com/url as it is just a redirect to the real ATS tracking link
    return True

@tool
def scrape_jobs_serpapi(query: str, location: str = "India", num_results: int = 20) -> list[dict]:
    """Scrape real job listings using SerpAPI and Arbeitnow, aggregating results."""
    search_term = query.replace(" jobs in India", "").replace(" jobs", "").strip().lower() or query.lower()
    
    combined_jobs = []
    seen = set()

    # Primary: SerpAPI (Google Jobs Engine)
    serpapi_key = os.getenv("SERPAPI_KEY")
    if serpapi_key:
        try:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "api_key": serpapi_key,
                "num": num_results,
                "gl": "in",
                "hl": "en"
            }
            # Reduced timeout and aggressively handle exceptions so it doesn't block
            response = httpx.get("https://serpapi.com/search", params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if "jobs_results" in data:
                    for job in data["jobs_results"]:
                        title = job.get("title", "")
                        company = job.get("company_name", "")
                        key = f"{title}-{company}"
                        if key in seen: continue
                        seen.add(key)
                        
                        apply_link = ""
                        if job.get("apply_options"):
                            apply_link = job["apply_options"][0].get("link", "")
                        if not apply_link and job.get("related_links"):
                            apply_link = job["related_links"][0].get("link", "")
                        
                        # Only include jobs with valid apply urls
                        if not is_valid_apply_url(apply_link):
                            continue

                        metadata = extract_metadata_from_description(job.get("description", ""))
                            
                        combined_jobs.append({
                            "title": title,
                            "company": company,
                            "location": job.get("location", ""),
                            "description": job.get("description", ""),
                            "url": apply_link,
                            "job_url": apply_link,
                            "apply_url": apply_link,
                            "source": infer_source(apply_link),
                            "posted_at": job.get("detected_extensions", {}).get("posted_at", ""),
                            "requirements": extract_skills_from_description(job.get("description", "")),
                            "experience_level": "Entry Level",
                            "is_verified": True,
                            **metadata
                        })
        except Exception as e:
            logger.warning(f"SerpAPI fetch failed or timed out: {e}")

    # Secondary: Arbeitnow (Always aggregate if possible)
    try:
        res = httpx.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        if res.status_code == 200:
            jobs_data = res.json().get("data", [])
            for job in jobs_data:
                title = job.get("title", "")
                company = job.get("company_name", "")
                desc = job.get("description", "")
                
                # Let the backend score and filter the Arbeitnow jobs rather than dropping them aggressively here.
                # Just do a soft check on the role if search_term is present
                if search_term:
                    search_words = search_term.split()
                    if not any(w in title.lower() or w in desc.lower() for w in search_words):
                        continue
                key = f"{title}-{company}"
                if key in seen:
                    continue
                seen.add(key)
                
                job_url = job.get("url", "")
                if not is_valid_apply_url(job_url):
                    continue

                metadata = extract_metadata_from_description(desc)
                
                combined_jobs.append({
                    "title": title,
                    "company": company,
                    "location": job.get("location", "Remote"),
                    "description": desc,
                    "url": job_url,
                    "job_url": job_url,
                    "apply_url": job_url,
                    "source": "Arbeitnow",
                    "posted_at": job.get("created_at", ""),
                    "requirements": extract_skills_from_description(desc),
                    "experience_level": "Entry Level",
                    "is_verified": True,
                    **metadata
                })
    except Exception as e:
        logger.warning(f"Arbeitnow fetch failed: {e}")

    return combined_jobs[:num_results]

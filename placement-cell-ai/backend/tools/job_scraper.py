import os
import httpx
from typing import Any
from langchain_core.tools import tool


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
        return "Other"


@tool
def scrape_jobs_serpapi(query: str, location: str = "India", num_results: int = 20) -> list[dict]:
    """Scrape job listings using SerpAPI Google Jobs search."""
    serpapi_key = os.getenv("SERPAPI_KEY")
    search_term = query.replace(" jobs in India", "").replace(" jobs", "").strip() or query
    
    if not serpapi_key:
        try:
            remotive_res = httpx.get(
                "https://remotive.com/api/remote-jobs",
                params={"search": search_term},
                timeout=30,
            )
            if remotive_res.status_code == 200:
                jobs_data = remotive_res.json().get("jobs", [])
                jobs = []
                seen = set()
                for job in jobs_data:
                    title = job.get("title", "")
                    company = job.get("company_name", "")
                    key = f"{title}-{company}"
                    if key in seen:
                        continue
                    seen.add(key)
                    description = job.get("description", "")
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": job.get("candidate_required_location", "Remote"),
                        "description": description,
                        "url": job.get("url", ""),
                        "source": "Remotive",
                        "posted_at": job.get("publication_date", ""),
                        "requirements": extract_skills_from_description(description),
                        "experience_level": "Entry Level",
                    })
                if jobs:
                    return jobs[:num_results]
        except Exception as e:
            logger.warning(f"Remotive fallback failed: {e}")

        return [
            {
                "title": "Python Backend Engineer Intern",
                "company": "TechCorp",
                "location": "Remote",
                "description": "We're looking for a Python backend engineer intern to work on our REST API.",
                "url": "https://example.com/job1",
                "source": "Demo",
                "posted_at": "3 days ago",
                "requirements": ["Python", "FastAPI", "SQL"],
                "experience_level": "Entry Level"
            },
            {
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "location": "Remote",
                "description": "Build modern web applications using React and Node.js.",
                "url": "https://example.com/job2",
                "source": "Demo",
                "posted_at": "1 week ago",
                "requirements": ["JavaScript", "React", "Node.js"],
                "experience_level": "Mid Level"
            }
        ]
    
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
        
        response = httpx.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "jobs_results" not in data:
            return []
        
        jobs = []
        seen = set()
        
        for job in data["jobs_results"]:
            title = job.get("title", "")
            company = job.get("company_name", "")
            key = f"{title}-{company}"
            
            if key in seen:
                continue
            seen.add(key)
            
            apply_link = ""
            if job.get("apply_options") and len(job["apply_options"]) > 0:
                apply_link = job["apply_options"][0].get("link", "")
            if not apply_link:
                apply_link = job.get("related_links", [{}])[0].get("link", "")
                
            job_dict = {
                "title": title,
                "company": company,
                "location": job.get("location", ""),
                "description": job.get("description", ""),
                "url": apply_link,
                "source": infer_source(apply_link),
                "posted_at": job.get("detected_extensions", {}).get("posted_at", ""),
                "requirements": extract_skills_from_description(job.get("description", "")),
                "experience_level": "Entry Level"
            }
            jobs.append(job_dict)
        
        return jobs
    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
        return []

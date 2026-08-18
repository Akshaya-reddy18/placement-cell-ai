import os
import httpx
import json
import logging
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger("github_tool")

@tool
def analyze_github_profile(github_username: str) -> dict:
    """Analyze a GitHub profile and return skill scores and domain expertise."""
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        return {
            "username": github_username,
            "bio": None,
            "public_repos": 0,
            "followers": 0,
            "total_stars": 0,
            "languages": {},
            "top_repos": [],
            "skill_scores": {},
            "domain_expertise": {"backend": 5, "frontend": 5, "ml": 2, "devops": 2, "mobile": 1},
            "profile_strength": 4,
            "notable_repos": [],
            "profile_summary": "GitHub analysis skipped because Gemini is unavailable.",
            "red_flags": [],
            "green_flags": [],
        }
    
    try:
        with httpx.Client(headers=headers, timeout=20.0) as client:
            # 1. Fetch user info
            user_res = client.get(f"https://api.github.com/users/{github_username}")
            if user_res.status_code == 404:
                return {"error": "GitHub user not found", "username": github_username}
            if user_res.status_code == 403:
                return {"error": "GitHub rate limit exceeded"}
            
            user_data = user_res.json()
            
            # 2. Fetch repos
            repos_res = client.get(f"https://api.github.com/users/{github_username}/repos?sort=pushed&per_page=30")
            repos = repos_res.json() if repos_res.status_code == 200 else []
            
            # 3. Aggregate stats
            repo_stats = []
            total_stars = 0
            languages_raw = {}
            
            for repo in repos:
                repo_info = {
                    "name": repo["name"],
                    "description": repo["description"],
                    "language": repo["language"],
                    "stars": repo["stargazers_count"],
                    "topics": repo.get("topics", []),
                    "updated_at": repo["updated_at"]
                }
                repo_stats.append(repo_info)
                total_stars += repo["stargazers_count"]
                
                # Fetch languages for top repos (limit to 5 to avoid rate limits)
                if len(repo_stats) <= 5:
                    lang_res = client.get(repo["languages_url"])
                    if lang_res.status_code == 200:
                        repo_langs = lang_res.json()
                        for lang, bytes_count in repo_langs.items():
                            languages_raw[lang] = languages_raw.get(lang, 0) + bytes_count
            
            stats = {
                "username": github_username,
                "bio": user_data.get("bio"),
                "public_repos": user_data.get("public_repos"),
                "followers": user_data.get("followers"),
                "total_stars": total_stars,
                "languages": languages_raw,
                "top_repos": repo_stats[:5]
            }
            
            # 4. Analyze with Gemini
            llm = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
                temperature=0
            )
            
            prompt = f"""You are a technical recruiter analyzing a GitHub profile. 
            Analyze this GitHub data and return ONLY valid JSON (no markdown backticks, no preamble):
            {{
              "skill_scores": {{"language": "score_1_to_10"}},
              "domain_expertise": {{"backend": 0-10, "frontend": 0-10, "ml": 0-10, "devops": 0-10, "mobile": 0-10}},
              "profile_strength": 0-10,
              "notable_repos": ["repo1", "repo2"],
              "profile_summary": "one paragraph summary",
              "red_flags": ["anything concerning"],
              "green_flags": ["standout qualities"]
            }}
            GitHub Data: {json.dumps(stats)}"""
            
            response = llm.invoke(prompt)
            clean_text = response.content.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            clean_text = clean_text.strip()
            
            ai_analysis = json.loads(clean_text)
            return {**stats, **ai_analysis}
            
    except Exception as e:
        logger.error(f"Error analyzing GitHub profile {github_username}: {e}")
        return {"error": str(e)}

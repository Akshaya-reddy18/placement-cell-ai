import os
import sys
from dotenv import load_dotenv

# Load backend .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", ".env"))

from backend.db.supabase_client import get_supabase_client
from backend.api.routes import _score_job, _fetch_live_jobs, _normalize_student_payload
from backend.tools.ats_tool import analyze_ats_compatibility, generate_optimized_resume
from backend.agents.ats_agent import ats_agent

def test_local_query_update():
    print("=== Testing _LocalQuery update ===")
    client = get_supabase_client()
    
    # Upsert a student
    client.table("students").upsert({
        "id": "test-student-1",
        "name": "Test Student",
        "email": "test@example.com",
        "resume_text": "Initial resume"
    }, on_conflict="id").execute()
    
    # Test update
    update_res = client.table("students").update({"resume_text": "Updated resume text with Python and ML"}).eq("id", "test-student-1").execute()
    print(f"Update succeeded: data={update_res.data}")
    assert update_res.data, "Update returned empty data"
    assert update_res.data[0]["resume_text"] == "Updated resume text with Python and ML"
    print("PASS: _LocalQuery.update works correctly!\n")

def test_personalization_diff():
    print("=== Testing Personalization for User A vs User B ===")
    
    user_a_context = {
        "student": {
            "id": "user-a",
            "name": "User A (ML Fresher)",
            "career_goals": {
                "preferred_roles": ["Machine Learning Engineer", "AI Engineer", "Python Developer"],
                "locations": ["Hyderabad"],
                "experience_level": "Fresher",
                "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning"],
                "target_companies": ["Google", "Microsoft"]
            }
        },
        "profile": {
            "skill_graph": {"Python": 9, "Machine Learning": 9, "TensorFlow": 8, "PyTorch": 8}
        },
        "career_goals": {
            "preferred_roles": ["Machine Learning Engineer", "AI Engineer", "Python Developer"],
            "locations": ["Hyderabad"],
            "experience_level": "Fresher",
            "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning"],
            "target_companies": ["Google", "Microsoft"]
        },
        "skill_graph": {"Python": 9, "Machine Learning": 9, "TensorFlow": 8, "PyTorch": 8}
    }

    user_b_context = {
        "student": {
            "id": "user-b",
            "name": "User B (Senior Java)",
            "career_goals": {
                "preferred_roles": ["Java Developer", "Backend Engineer", "Spring Boot Architect"],
                "locations": ["Bangalore"],
                "experience_level": "3+ years",
                "skills": ["Java", "Spring Boot", "Microservices", "PostgreSQL"],
                "target_companies": ["Amazon", "Razorpay"]
            }
        },
        "profile": {
            "skill_graph": {"Java": 9, "Spring Boot": 9, "Microservices": 8, "PostgreSQL": 8}
        },
        "career_goals": {
            "preferred_roles": ["Java Developer", "Backend Engineer", "Spring Boot Architect"],
            "locations": ["Bangalore"],
            "experience_level": "3+ years",
            "skills": ["Java", "Spring Boot", "Microservices", "PostgreSQL"],
            "target_companies": ["Amazon", "Razorpay"]
        },
        "skill_graph": {"Java": 9, "Spring Boot": 9, "Microservices": 8, "PostgreSQL": 8}
    }

    test_jobs = [
        {
            "id": "job-ml-1",
            "title": "Junior Machine Learning Engineer",
            "company": "Google",
            "location": "Hyderabad",
            "description": "We are seeking a Junior ML Engineer proficient in Python, TensorFlow, and PyTorch. Fresher / Entry Level welcome.",
            "requirements": ["Python", "TensorFlow", "Machine Learning"],
            "experience_level": "Entry Level",
            "work_mode": "Hybrid",
            "employment_type": "Full-time",
            "company_type": "FAANG",
            "url": "https://careers.google.com/jobs/results/123",
            "apply_url": "https://careers.google.com/jobs/results/123",
            "posted_at": "2 days ago"
        },
        {
            "id": "job-java-1",
            "title": "Senior Java Backend Engineer",
            "company": "Amazon",
            "location": "Bangalore",
            "description": "Amazon is hiring a Senior Java Developer with 3+ years experience in Spring Boot, Microservices, and SQL architecture.",
            "requirements": ["Java", "Spring Boot", "Microservices"],
            "experience_level": "Senior",
            "work_mode": "On-site",
            "employment_type": "Full-time",
            "company_type": "FAANG",
            "url": "https://amazon.jobs/en/jobs/456",
            "apply_url": "https://amazon.jobs/en/jobs/456",
            "posted_at": "1 day ago"
        }
    ]

    score_a_ml, reason_a_ml = _score_job(test_jobs[0], user_a_context)
    score_a_java, reason_a_java = _score_job(test_jobs[1], user_a_context)

    score_b_ml, reason_b_ml = _score_job(test_jobs[0], user_b_context)
    score_b_java, reason_b_java = _score_job(test_jobs[1], user_b_context)

    print(f"User A (ML Fresher):")
    print(f"  ML Job Score: {score_a_ml}% (Reason: {reason_a_ml})")
    print(f"  Java Job Score: {score_a_java}% (Reason: {reason_a_java})")

    print(f"User B (Java 3+ years):")
    print(f"  ML Job Score: {score_b_ml}% (Reason: {reason_b_ml})")
    print(f"  Java Job Score: {score_b_java}% (Reason: {reason_b_java})")

    assert score_a_ml > score_a_java, f"User A should score ML job higher than Java job: {score_a_ml} vs {score_a_java}"
    assert score_b_java > score_b_ml, f"User B should score Java job higher than ML job: {score_b_java} vs {score_b_ml}"
    assert score_a_ml != score_b_ml, "Different users must have different scores for the same job!"
    
    print("PASS: User personalization generates distinctly different rankings!\n")

def test_ats_agent_flow():
    print("=== Testing ATS Agent Flow ===")
    state = {
        "student_id": "test-student-ats",
        "student_data": {
            "resume_text": "Experienced Python and Fast API developer with background in building REST APIs, Docker, and PostgreSQL databases.",
            "career_goals": {
                "preferred_roles": ["Python Backend Developer"],
                "target_companies": ["Stripe"]
            }
        },
        "matched_jobs": [],
        "analysis_status": {
            "current_agent": "starting",
            "completed_agents": [],
            "percentage": 0,
            "status": "running"
        },
        "messages": []
    }
    
    result_state = ats_agent(state)
    versions = result_state.get("resume_versions", [])
    print(f"Generated {len(versions)} resume versions.")
    assert len(versions) > 0, "ATS agent failed to produce resume versions"
    print(f"Latest ATS Score: {versions[0].get('ats_score')}")
    print(f"Present keywords: {versions[0].get('present_keywords')}")
    print(f"Missing keywords: {versions[0].get('missing_keywords')}")
    print("PASS: ATS agent runs and stores resume version!\n")

if __name__ == "__main__":
    test_local_query_update()
    test_personalization_diff()
    test_ats_agent_flow()
    print("ALL TESTS PASSED SUCCESSFULLY!")

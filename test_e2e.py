import time
import requests
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("Starting E2E Tests...")
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    # 1. Test New Student Pipeline
    print(f"Testing Onboarding for {test_email}...")
    student_payload = {
        "name": "E2E Test User",
        "email": test_email,
        "phone": "1234567890",
        "college": "Test Institute",
        "branch": "Computer Science",
        "graduation_year": 2026,
        "cgpa": "8.5",
        "resume_text": "Experienced in Python, React, and Machine Learning.",
        "skills": ["Python", "React", "Machine Learning"],
        "career_goals": {
            "preferred_roles": ["Software Engineer", "AI Engineer"],
            "locations": ["Bangalore", "Remote"],
            "work_mode": ["Remote"],
            "employment_type": ["Full-time"],
            "company_type": ["Startup"],
            "target_companies": ["Google", "OpenAI"]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/students", json=student_payload)
        response.raise_for_status()
        student_data = response.json()
        student_id = student_data["id"]
        print(f"[SUCCESS] Onboarding successful. Student ID: {student_id}")
    except Exception as e:
        print(f"[FAIL] Onboarding failed: {e}")
        if 'response' in locals(): print(response.text)
        sys.exit(1)

    # 2. Test AI Status Polling
    print("Testing AI Status Polling...")
    for _ in range(60):
        try:
            status_res = requests.get(f"{BASE_URL}/api/status", headers={"X-Student-Id": student_id})
            status_res.raise_for_status()
            status_data = status_res.json()
            print(f"Status: {status_data['status']} ({status_data.get('percentage', 0)}%)")
            if status_data["status"] == "completed":
                print("[SUCCESS] AI Pipeline completed.")
                break
            elif status_data["status"] == "failed":
                print(f"[FAIL] AI Pipeline failed: {status_data.get('error_message')}")
                break
            time.sleep(3)
        except Exception as e:
            print(f"[FAIL] Status check failed: {e}")
            break

    # 3. Test Jobs Fetching & Filtering
    print("Testing Jobs API...")
    try:
        jobs_res = requests.get(f"{BASE_URL}/api/jobs", headers={"X-Student-Id": student_id})
        jobs_res.raise_for_status()
        jobs = jobs_res.json()
        print(f"[SUCCESS] Jobs fetched successfully. Count: {len(jobs)}")
        if jobs:
            print(f"First job: {jobs[0].get('title')} at {jobs[0].get('company')}")
    except Exception as e:
        print(f"[FAIL] Jobs fetch failed: {e}")

    # 4. Test Mock Interview Flow
    print("Testing Mock Interview Chat...")
    chat_payload = {
        "student_id": student_id,
        "history": [
            {"role": "assistant", "content": "Hello! I am your AI interviewer. Are you ready to begin our mock interview session?"},
            {"role": "user", "content": "Yes, I am ready."}
        ]
    }
    try:
        chat_res = requests.post(f"{BASE_URL}/api/interview/chat", json=chat_payload, headers={"X-Student-Id": student_id})
        chat_res.raise_for_status()
        chat_data = chat_res.json()
        print(f"[SUCCESS] Chat successful. Reply: {chat_data.get('reply')}")
    except Exception as e:
        print(f"[FAIL] Chat failed: {e}")

    print("\nE2E Tests Finished.")

if __name__ == "__main__":
    run_tests()

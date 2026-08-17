import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_insert():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(url, key)
    
    student_data = {
        "name": "Test Student",
        "email": "test@example.com",
        "college": "Test University",
        "branch": "CS",
        "graduation_year": 2026
    }
    
    try:
        # Try to insert
        res = supabase.table("students").upsert(student_data, on_conflict="email").execute()
        print(f"Insert result: {res.data}")
        
        if res.data:
            student_id = res.data[0]["id"]
            # Try to update status
            status_res = supabase.table("analysis_status").upsert({
                "student_id": student_id,
                "current_agent": "starting",
                "percentage": 0,
                "status": "pending"
            }).execute()
            print(f"Status update result: {status_res.data}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_insert()

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    print(f"URL: {url}")
    print(f"Key exists: {key is not None}")
    
    try:
        supabase = create_client(url, key)
        # Try to select from students table
        res = supabase.table("students").select("count", count="exact").limit(0).execute()
        print("Successfully connected to Supabase and accessed 'students' table.")
        print(f"Table count: {res.count}")
        
        # Check analysis_status
        res_status = supabase.table("analysis_status").select("count", count="exact").limit(0).execute()
        print("Successfully accessed 'analysis_status' table.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_supabase()

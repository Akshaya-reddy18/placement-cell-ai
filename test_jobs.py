import httpx

try:
    print("Fetching jobs from backend...")
    res = httpx.get("http://localhost:8000/api/jobs", timeout=120.0)
    print(f"Status Code: {res.status_code}")
    jobs = res.json()
    if isinstance(jobs, dict) and 'jobs' in jobs:
        jobs = jobs['jobs']
    print(f"Total jobs returned: {len(jobs)}")
    for j in jobs[:5]:
        print(f"\n{j.get('title', 'N/A')} @ {j.get('company', 'N/A')}")
        print(f"  Score: {j.get('matchPercentage', 0)}% - {j.get('matchReason', 'N/A')}")
        print(f"  Apply URL: {j.get('apply_url', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

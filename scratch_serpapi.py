import os, httpx, json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))
key = os.getenv('SERPAPI_KEY')
print(f"Key exists: {key is not None}")
if key:
    res = httpx.get('https://serpapi.com/search', params={'engine': 'google_jobs', 'q': 'Software Engineer jobs', 'api_key': key, 'gl': 'in', 'hl': 'en', 'num': 2}, timeout=30)
    print(json.dumps(res.json(), indent=2)[:2000])

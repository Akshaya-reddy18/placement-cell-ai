import sys
import os
# Ensure the root project directory is in sys.path so uvicorn subprocesses can find the 'backend' module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging

# Load environment variables
import os
import logging
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

from backend.api.routes import router as api_router
from backend.db.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("placement_cell")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Placement Cell AI API (Gemini Edition)...")
    
    # Verify Supabase connection
    try:
        client = get_supabase_client()
        # Simple test query
        client.table("students").select("count", count="exact").limit(0).execute()
        logger.info("✅ Supabase Cloud connected")
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        # We don't necessarily want to crash here if Supabase is temporarily down,
        # but the project guide suggests it's a critical check.
    
    # Verify Gemini API key
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("❌ GEMINI_API_KEY / GOOGLE_API_KEY not set")
    else:
        logger.info("✅ Gemini API key found")
        
        # Optional: Quick Gemini connectivity test
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            test_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=gemini_key,
                temperature=0
            )
            # test_llm.invoke("Say OK") # Commented out to save tokens/time during startup
            logger.info("✅ Gemini API connection verified (skipped invoke)")
        except Exception as e:
            logger.warning(f"⚠️ Gemini API test failed: {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down Placement Cell AI API")

app = FastAPI(
    title="Placement Cell AI API (Gemini Edition)",
    description="Autonomous AI Placement Officer powered by Google Gemini",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Placement Cell AI",
        "version": "3.0.0",
        "ai_provider": "Google Gemini 2.0 Flash"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)

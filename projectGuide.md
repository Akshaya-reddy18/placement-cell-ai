# Autonomous Placement Cell AI — Complete Build Guide v3 (Gemini Edition)
### Step-by-Step with Exact Prompts | Supabase Cloud + Render + Vercel | Google Gemini API

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│          Vercel (Frontend)                              │
│   React + TypeScript + Tailwind + Shadcn UI             │
│   https://placement-cell-ai.vercel.app                  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API calls
┌──────────────────────▼──────────────────────────────────┐
│          Render (Backend)                               │
│   FastAPI + Python                                      │
│   https://placement-cell-api.onrender.com               │
│                                                         │
│   LangGraph Orchestrator                                │
│   └── 8 AI Agents (LangChain + Google Gemini 2.0 Flash) │
└──────────────────────┬──────────────────────────────────┘
                       │ DB queries + vector search
┌──────────────────────▼──────────────────────────────────┐
│          Supabase Cloud (Free Tier)                     │
│   PostgreSQL + pgvector + Auth + Storage                │
│   https://xxxx.supabase.co                              │
└─────────────────────────────────────────────────────────┘
```

**Cost: $0/month** for the entire stack during development and demo.
**Gemini 2.0 Flash** — free tier gives 15 RPM, 1M TPM, 1500 requests/day. More than enough for dev + demo.

---

## GEMINI API — QUICK REFERENCE

| Feature | Value |
|---|---|
| Model used | `gemini-2.0-flash` |
| LangChain package | `langchain-google-genai` |
| Embedding model | `models/text-embedding-004` |
| Embedding dimensions | `768` (NOT 1536 like OpenAI) |
| Free tier | 15 RPM · 1M TPM · 1500 req/day |
| API key source | https://aistudio.google.com/apikey |
| Environment variable | `GEMINI_API_KEY` |

> ⚠️ **IMPORTANT:** Gemini embeddings produce **768-dimensional vectors**, not 1536. The `pgvector` column `embedding vector(768)` must be used everywhere — not `vector(1536)`.

---

## PHASE 0: ACCOUNTS & ENVIRONMENT SETUP

### Step 0.1 — Create All Cloud Accounts First
Do this before writing any code. You need these URLs and keys upfront.

**A) Supabase Cloud**
1. Go to https://supabase.com → Sign Up (use GitHub login)
2. Click "New Project"
3. Fill in:
   - Organization: your name or college name
   - Project name: `placement-cell-ai`
   - Database password: create a strong password, **save it somewhere**
   - Region: **Southeast Asia (Singapore)** — closest to India
4. Click "Create new project" — wait 2 minutes for provisioning
5. Once ready, go to **Settings → API**
6. Copy and save these values:
   - **Project URL** → looks like `https://abcdefghij.supabase.co`
   - **anon public** key → long JWT starting with `eyJ...`
   - **service_role** key → another long JWT (keep this secret — backend only)
7. Go to **Settings → Database**
8. Copy and save the **Connection string (URI)** → `postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghij.supabase.co:5432/postgres`

**B) Render**
1. Go to https://render.com → Sign Up (use GitHub login)
2. No setup needed yet — you'll come back here in Phase 10

**C) Vercel**
1. Go to https://vercel.com → Sign Up (use GitHub login)
2. No setup needed yet — you'll come back here in Phase 10

**D) Google AI Studio (Gemini API) ← replaces OpenAI**
1. Go to https://aistudio.google.com/apikey
2. Click **Create API Key** → Select a Google Cloud project (or create new)
3. Copy and save the key starting with `AIza...`
4. No billing required — free tier is sufficient for development

**E) SerpAPI** (for job scraping)
1. Go to https://serpapi.com → Sign Up
2. Free tier gives 100 searches/month
3. Copy your API key from the dashboard

**F) GitHub**
1. Go to https://github.com/settings/tokens → Generate new token (classic)
2. Select scope: `public_repo` only
3. Copy and save the token (increases GitHub API rate limit from 60 to 5000 req/hour)

---

### Step 0.2 — Install Local Prerequisites
Run these in your terminal:
```bash
# Check versions
node -v          # need v18+
python --version # need 3.11+
git --version

# Install uv (fast Python package manager)
pip install uv

# Install Supabase CLI (for running migrations)
npm install -g supabase

# Verify Supabase CLI installed
supabase --version
```

---

### Step 0.3 — Create Project Folder Structure
Open VS Code / Cursor / Trae in an empty folder called `placement-cell-ai`.

**Prompt — paste this in Cursor Chat (Ctrl+L) or Trae Chat:**
```
Create the complete folder structure for an Autonomous Placement Cell AI project.
Create all folders and empty placeholder files as described. Do NOT write any logic yet.

Root structure:
/placement-cell-ai
  /backend
    /agents
      __init__.py
      profile_agent.py
      job_match_agent.py
      ats_agent.py
      skill_gap_agent.py
      interview_agent.py
      referral_agent.py
      career_strategy_agent.py
      tracking_agent.py
      recruiter_simulator.py
      probability_predictor.py
    /graph
      __init__.py
      placement_graph.py
    /tools
      __init__.py
      resume_parser.py
      github_tool.py
      ats_tool.py
      job_scraper.py
      semantic_search.py
      interview_tool.py
    /api
      __init__.py
      routes.py
    /db
      __init__.py
      supabase_client.py
      schema.sql
      migrations.sql
    /schemas
      __init__.py
      state.py
    /tests
      __init__.py
      test_pipeline.py
    main.py
    requirements.txt
    .env
    .env.example
    .gitignore
    Dockerfile
    render.yaml
  /frontend
    /src
      /components
        /ui        (shadcn components go here)
        Sidebar.tsx
        AgentStatus.tsx
        JobCard.tsx
        SkillBadge.tsx
      /pages
        Onboarding.tsx
        Dashboard.tsx
        Jobs.tsx
        Resume.tsx
        Skills.tsx
        Interview.tsx
        Referrals.tsx
        Strategy.tsx
        Applications.tsx
      /hooks
        useAnalysisProgress.ts
        useStudent.ts
      /lib
        api.ts
        utils.ts
      /store
        useStore.ts
      App.tsx
      main.tsx
    index.html
    vite.config.ts
    tailwind.config.ts
    tsconfig.json
    .env
    .env.example
    vercel.json
    .gitignore
  README.md
  .gitignore

After creating the structure, also create a root .gitignore that ignores:
.env files, __pycache__, node_modules, .venv, dist, build, *.pyc
```

---

### Step 0.4 — Install Python Dependencies
**Run in terminal inside `/backend` folder:**
```bash
uv venv .venv
source .venv/bin/activate   # Mac/Linux
# OR
.venv\Scripts\activate      # Windows

uv pip install \
  langchain==0.2.16 \
  langgraph==0.2.28 \
  langchain-google-genai==1.0.10 \
  langchain-community==0.2.16 \
  langchain-core==0.2.38 \
  google-generativeai==0.7.2 \
  fastapi==0.115.0 \
  uvicorn==0.30.6 \
  supabase==2.7.4 \
  python-dotenv==1.0.1 \
  pydantic==2.8.2 \
  PyMuPDF==1.24.10 \
  httpx==0.27.2 \
  python-multipart==0.0.9 \
  pytest==8.3.3 \
  pytest-asyncio==0.24.0

# Save to requirements.txt
uv pip freeze > requirements.txt
```

> **Key change from v2:** `langchain-openai` and `openai` are replaced by `langchain-google-genai` and `google-generativeai`.

---

### Step 0.5 — Install Frontend Dependencies
**Run in terminal inside `/frontend` folder:**
```bash
npm create vite@latest . -- --template react-ts
npm install
npx shadcn@latest init
# When prompted: Default style, Slate color, yes to CSS variables

npm install \
  @tanstack/react-query \
  axios \
  zustand \
  react-router-dom \
  recharts \
  lucide-react \
  @dnd-kit/core \
  @dnd-kit/sortable \
  @dnd-kit/utilities \
  clsx \
  tailwind-merge
```

---

### Step 0.6 — Create Environment Files

**Create `/backend/.env` — fill in YOUR actual values from Step 0.1:**
```env
# ─────────────────────────────────────────────
# Google Gemini API  ← replaces OPENAI_API_KEY
# ─────────────────────────────────────────────
GEMINI_API_KEY=AIzaSyYour-actual-gemini-key-here

# ─────────────────────────────────────────────
# Supabase Cloud
# ─────────────────────────────────────────────
SUPABASE_URL=https://abcdefghij.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-anon-key
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-service-role-key
SUPABASE_DB_URL=postgresql://postgres:YOUR-DB-PASSWORD@db.abcdefghij.supabase.co:5432/postgres

# ─────────────────────────────────────────────
# SerpAPI (job scraping)
# ─────────────────────────────────────────────
SERPAPI_KEY=your-serpapi-key-here

# ─────────────────────────────────────────────
# GitHub (optional — increases rate limit)
# ─────────────────────────────────────────────
GITHUB_TOKEN=ghp_your-github-token-here

# ─────────────────────────────────────────────
# App Config
# ─────────────────────────────────────────────
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173

# ─────────────────────────────────────────────
# Gemini Model Settings (change if needed)
# ─────────────────────────────────────────────
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
```

**Create `/backend/.env.example` — safe to commit to GitHub:**
```env
# Google Gemini API key (get from https://aistudio.google.com/apikey)
GEMINI_API_KEY=AIzaSy...

# Supabase Cloud
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# SerpAPI (https://serpapi.com)
SERPAPI_KEY=...

# GitHub Personal Access Token (optional)
GITHUB_TOKEN=ghp_...

# App Configuration
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173

# Gemini model identifiers
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
```

**Create `/frontend/.env`:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://abcdefghij.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-anon-key
```

**Create `/frontend/.env.example`:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

---

## PHASE 1: SUPABASE CLOUD DATABASE SETUP

> ⚠️ Everything in this phase runs directly on Supabase Cloud — NOT locally.
> You will paste SQL into the Supabase Dashboard SQL Editor.

> ⚠️ **Gemini Change:** All `vector(1536)` columns become `vector(768)` because Gemini's `text-embedding-004` model outputs 768-dimensional vectors.

### Step 1.1 — Enable pgvector Extension
1. Go to your Supabase project dashboard
2. Click **Database** in left sidebar → **Extensions**
3. Search for "vector"
4. Click the toggle to enable **vector** extension
5. Confirm — wait 10 seconds

### Step 1.2 — Create Full Database Schema
**Prompt for Cursor (open `/backend/db/schema.sql`):**
```
Write a complete, production-ready Supabase PostgreSQL schema for a Placement Cell AI platform.
This will be run directly in the Supabase Cloud SQL Editor.
IMPORTANT: Use vector(768) everywhere — NOT vector(1536).
This is because we use Google Gemini text-embedding-004 which outputs 768-dim vectors.

Requirements:

1. Enable extensions at the top:
   - vector (for pgvector — already enabled, but add the statement anyway)
   - uuid-ossp (for gen_random_uuid())

2. Create these tables in order (respecting foreign keys):

TABLE: students
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - name text NOT NULL
  - email text UNIQUE NOT NULL
  - college text
  - branch text
  - graduation_year int
  - github_url text
  - linkedin_url text
  - resume_url text  (Supabase Storage URL)
  - resume_text text  (extracted text content)
  - career_goals jsonb  (preferred_roles, target_companies, work_preference, location)
  - created_at timestamptz DEFAULT now()
  - updated_at timestamptz DEFAULT now()

TABLE: student_profiles
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - skill_graph jsonb  (e.g. {"Python": 8, "React": 6})
  - career_profile jsonb
  - domain_scores jsonb  (e.g. {"backend": 8, "frontend": 5, "ml": 3})
  - strength_analysis text
  - profile_completeness int DEFAULT 0
  - created_at timestamptz DEFAULT now()
  - updated_at timestamptz DEFAULT now()

TABLE: jobs
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - title text NOT NULL
  - company text NOT NULL
  - source text  (linkedin/wellfound/internshala/other)
  - url text
  - description text
  - requirements jsonb
  - location text
  - experience_level text  (intern/junior/mid/senior)
  - posted_at timestamptz
  - scraped_at timestamptz DEFAULT now()
  - is_active boolean DEFAULT true

TABLE: job_embeddings
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - job_id uuid REFERENCES jobs(id) ON DELETE CASCADE
  - embedding vector(768)   ← 768 for Gemini text-embedding-004
  - created_at timestamptz DEFAULT now()

TABLE: student_embeddings
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - embedding vector(768)   ← 768 for Gemini text-embedding-004
  - created_at timestamptz DEFAULT now()

TABLE: job_matches
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - job_id uuid REFERENCES jobs(id) ON DELETE CASCADE
  - match_percentage numeric(5,2)
  - eligibility_notes text
  - priority_rank text  (high/medium/low)
  - created_at timestamptz DEFAULT now()
  - UNIQUE(student_id, job_id)

TABLE: resume_versions
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - job_id uuid REFERENCES jobs(id) ON DELETE CASCADE
  - ats_score numeric(5,2)
  - missing_keywords jsonb
  - present_keywords jsonb
  - suggestions jsonb
  - optimized_resume_text text
  - original_resume_text text
  - created_at timestamptz DEFAULT now()

TABLE: skill_gaps
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - critical_missing jsonb
  - nice_to_have jsonb
  - emerging_trends jsonb
  - learning_roadmap jsonb
  - weekly_plans jsonb
  - certifications jsonb
  - created_at timestamptz DEFAULT now()
  - updated_at timestamptz DEFAULT now()

TABLE: interview_sessions
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - session_type text  (prep/mock)
  - questions_bank jsonb
  - mock_answers jsonb
  - feedback jsonb
  - confidence_score numeric(5,2)
  - readiness_score numeric(5,2)
  - weak_areas jsonb
  - strong_areas jsonb
  - created_at timestamptz DEFAULT now()

TABLE: referrals
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - company text
  - target_role text
  - connection_type text  (alumni/recruiter/engineer/hiring_manager)
  - outreach_templates jsonb
  - referral_pathway jsonb
  - created_at timestamptz DEFAULT now()

TABLE: career_strategies
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - target_companies jsonb
  - focus_recommendation text
  - skill_roi jsonb
  - placement_probability numeric(5,2)
  - action_plan_90_days jsonb
  - red_flags jsonb
  - quick_wins jsonb
  - created_at timestamptz DEFAULT now()

TABLE: applications
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE
  - job_id uuid REFERENCES jobs(id) ON DELETE CASCADE
  - status text DEFAULT 'applied'  (applied/oa/interview/offer/rejected)
  - applied_at timestamptz DEFAULT now()
  - last_updated timestamptz DEFAULT now()
  - notes text
  - UNIQUE(student_id, job_id)

TABLE: analysis_status
  - id uuid PRIMARY KEY DEFAULT gen_random_uuid()
  - student_id uuid REFERENCES students(id) ON DELETE CASCADE UNIQUE
  - current_agent text
  - completed_agents jsonb DEFAULT '[]'
  - percentage int DEFAULT 0
  - status text DEFAULT 'pending'  (pending/running/completed/failed)
  - started_at timestamptz DEFAULT now()
  - completed_at timestamptz

3. Create indexes:
   - students(email)
   - job_matches(student_id), job_matches(job_id)
   - applications(student_id), applications(status)
   - job_embeddings using ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
   - student_embeddings using ivfflat (embedding vector_cosine_ops) WITH (lists = 100)

4. Create updated_at auto-update trigger function and apply to all tables with updated_at column.

5. Create this RPC function for semantic job search:
   match_jobs(query_embedding vector(768), match_threshold float, match_count int)
   Returns: job_id, title, company, description, similarity
   Uses cosine similarity: 1 - (job_embeddings.embedding <=> query_embedding)
   Filter: similarity >= match_threshold
   Order by similarity DESC
   Limit to match_count
```

---

## PHASE 2: PYDANTIC SCHEMAS

### Step 2.1 — Agent State and Models
**Prompt for Cursor (open `/backend/schemas/state.py`):**
```
Write all Pydantic v2 schemas and LangGraph state for the Placement Cell AI.
No changes needed here from the original design — this is model-agnostic.

Part 1: LangGraph AgentState (TypedDict)
Fields:
- student_id: str
- student_data: dict
- skill_graph: dict
- domain_scores: dict
- job_listings: list[dict]
- matched_jobs: list[dict]
- resume_versions: list[dict]
- skill_gaps: dict
- interview_prep: dict
- referrals: list[dict]
- career_strategy: dict
- applications: list[dict]
- analysis_status: dict
- error: str | None
- messages: list[dict]

Part 2: Pydantic BaseModel classes (same as original — StudentInput, JobListing, JobMatch,
ResumeVersion, SkillGapReport, InterviewQuestion, InterviewFeedback, CareerStrategy,
AnalysisStatusResponse)

Add model_config with json_schema_extra examples for each model.
Use field validators where appropriate.
```

---

## PHASE 3: LANGCHAIN TOOLS (GEMINI VERSIONS)

> **Key Import Change:**
> - Replace `from langchain_openai import ChatOpenAI` with `from langchain_google_genai import ChatGoogleGenerativeAI`
> - Replace `from langchain_openai import OpenAIEmbeddings` with `from langchain_google_genai import GoogleGenerativeAIEmbeddings`
> - Replace `model="gpt-4o"` with `model="gemini-2.0-flash"`
> - Replace `model="text-embedding-3-small"` with `model="models/text-embedding-004"`

### Step 3.1 — Resume Parser Tool
**Prompt for Cursor (open `/backend/tools/resume_parser.py`):**
```
Write a LangChain Tool for parsing resumes using PyMuPDF and Google Gemini.

Requirements:
- Import: from langchain_core.tools import tool
- from langchain_google_genai import ChatGoogleGenerativeAI
- from langchain_core.output_parsers import JsonOutputParser
- import fitz  (PyMuPDF)
- import os

@tool
def parse_resume_pdf(pdf_path: str) -> dict:
  """Parse a PDF resume file and extract structured information."""
  - Use fitz.open(pdf_path) to extract all text from all pages
  - Concatenate text from all pages
  - Pass to extract_resume_data()

@tool
def parse_resume_text(resume_text: str) -> dict:
  """Parse resume text and extract structured information using Gemini AI."""
  - Calls extract_resume_data(resume_text) directly

def extract_resume_data(resume_text: str) -> dict:
  - Create ChatGoogleGenerativeAI(
      model="gemini-2.0-flash",
      google_api_key=os.getenv("GEMINI_API_KEY"),
      temperature=0
    )
  - System prompt (use HumanMessage since Gemini handles system via first human message):
    "You are a resume parser. Extract information exactly as it appears. Return ONLY valid JSON with no markdown, no backticks."
  - User prompt:
    """Extract from this resume and return as JSON only (no markdown):
    {
      "name": "full name",
      "email": "email address",
      "phone": "phone number",
      "location": "city/state",
      "summary": "professional summary if present",
      "skills": ["list", "of", "skills"],
      "experience": [
        {"company": "", "role": "", "duration": "", "start_date": "", "end_date": "", "description": "bullet points", "tech_used": []}
      ],
      "education": [
        {"institution": "", "degree": "", "field": "", "year": "", "cgpa": ""}
      ],
      "projects": [
        {"name": "", "description": "", "tech_stack": [], "url": "", "github": ""}
      ],
      "certifications": [{"name": "", "issuer": "", "year": ""}],
      "achievements": ["list of achievements"],
      "languages": ["programming languages only"]
    }
    Resume text:
    {resume_text}"""
  - Use JsonOutputParser to parse response
  - Return the parsed dict
  - On error: return {"error": str(e), "raw_text": resume_text[:500]}

NOTE for Gemini: Strip any leading/trailing markdown code fences (```json ... ```) from the
response before passing to JsonOutputParser, as Gemini sometimes includes them despite instructions.
Use: clean_text = response.content.strip().strip("```json").strip("```").strip()
```

### Step 3.2 — GitHub Analysis Tool
**Prompt for Cursor (open `/backend/tools/github_tool.py`):**
```
Write a LangChain Tool for analyzing GitHub profiles.

Requirements:
- Use httpx for HTTP requests
- Use GITHUB_TOKEN from environment for Authorization header
- from langchain_google_genai import ChatGoogleGenerativeAI
- from langchain_core.output_parsers import JsonOutputParser
- import os

@tool
def analyze_github_profile(github_username: str) -> dict:
  """Analyze a GitHub profile and return skill scores and domain expertise."""

  Implementation:
  1. Fetch user info: GET https://api.github.com/users/{username}
     Headers: {"Authorization": f"token {GITHUB_TOKEN}"} if token exists
     Extract: public_repos, followers, created_at, bio
  
  2. Fetch repos: GET https://api.github.com/users/{username}/repos?sort=pushed&per_page=30
     For each repo extract: name, description, language, stargazers_count, topics, updated_at
  
  3. Fetch languages for top 10 repos: GET https://api.github.com/repos/{username}/{repo}/languages
     Aggregate bytes per language across all repos
  
  4. Compute raw stats:
     - total_stars = sum of all repo stars
     - language_percentages = each language's bytes / total bytes * 100
     - active_repos = repos updated in last 6 months
     - top_topics = most common repo topics
  
  5. Send stats to Gemini for analysis:
     llm = ChatGoogleGenerativeAI(
       model="gemini-2.0-flash",
       google_api_key=os.getenv("GEMINI_API_KEY"),
       temperature=0
     )
     Prompt: "You are a technical recruiter analyzing a GitHub profile. 
     Analyze this GitHub data and return ONLY JSON (no markdown backticks):
     {
       'skill_scores': {'language': score_1_to_10},
       'domain_expertise': {'backend': 0-10, 'frontend': 0-10, 'ml': 0-10, 'devops': 0-10, 'mobile': 0-10},
       'profile_strength': 0-10,
       'notable_repos': ['repo1', 'repo2'],
       'profile_summary': 'one paragraph',
       'red_flags': ['anything concerning'],
       'green_flags': ['standout qualities']
     }
     GitHub Data: {stats}"
  
  6. Strip markdown code fences before parsing JSON response
  7. Return merged dict: raw_stats + ai_analysis
  
  Error handling:
  - If username not found (404): return {"error": "GitHub user not found", "username": github_username}
  - If rate limited (403): return {"error": "GitHub rate limit exceeded"}
  - If no GITHUB_TOKEN: proceed anyway (lower rate limit)
```

### Step 3.3 — ATS Analysis Tool
**Prompt for Cursor (open `/backend/tools/ats_tool.py`):**
```
Write a LangChain Tool for ATS resume analysis and optimization using Google Gemini.

Requirements:
- from langchain_google_genai import ChatGoogleGenerativeAI
- from langchain_core.output_parsers import JsonOutputParser
- import os

def get_llm():
  return ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )

@tool
def analyze_ats_compatibility(resume_text: str, job_description: str, job_title: str = "", company: str = "") -> dict:
  """Analyze resume against a job description for ATS compatibility and suggest optimizations."""
  
  llm = get_llm()
  
  Prompt (single HumanMessage combining system + user context):
  """You are an expert ATS analyst with deep knowledge of how recruiting software screens resumes.
  You know the exact keyword matching algorithms used by Workday, Greenhouse, Lever, and Taleo.
  
  Analyze this resume against the job description for ATS compatibility.
  Return ONLY this JSON (no markdown backticks, no preamble):
  
  JOB TITLE: {job_title} at {company}
  
  JOB DESCRIPTION:
  {job_description}
  
  RESUME:
  {resume_text}
  
  {{
    "ats_score": <0-100>,
    "keyword_match_rate": <percentage>,
    "missing_keywords": [<critical keywords from JD missing in resume>],
    "present_keywords": [<JD keywords already in resume>],
    "suggestions": [<specific actionable changes>],
    "optimized_summary": "<rewrite resume summary for this JD>",
    "section_scores": {{
      "skills": <0-100>,
      "experience": <0-100>,
      "education": <0-100>,
      "projects": <0-100>
    }},
    "formatting_issues": [<any formatting problems that hurt ATS>],
    "optimized_skills_section": "<rewritten skills section with missing keywords added>"
  }}"""
  
  Strip markdown code fences from response, then parse JSON.
  On error return: {"ats_score": 0, "error": str(e)}

@tool
def generate_optimized_resume(original_resume: str, job_description: str, ats_analysis: dict) -> str:
  """Generate a fully optimized resume version for a specific job using Gemini."""
  
  llm = get_llm()
  Use Gemini to rewrite full resume incorporating:
  - All missing_keywords from ats_analysis naturally integrated
  - Optimized summary from ats_analysis
  - Quantified achievements where possible
  - Job-relevant skills highlighted
  
  Return the optimized resume as clean markdown text.
```

### Step 3.4 — Job Scraping Tool
**Prompt for Cursor (open `/backend/tools/job_scraper.py`):**
```
Write a LangChain Tool for scraping jobs using SerpAPI Google Jobs.
(This tool is model-agnostic — no Gemini changes needed here.)

Requirements:
- Use httpx for HTTP requests
- Use SERPAPI_KEY from environment
- Return structured job listings

@tool
def scrape_jobs_serpapi(query: str, location: str = "India", num_results: int = 20) -> list[dict]:
  """Scrape job listings using SerpAPI Google Jobs search."""
  
  Build SerpAPI request:
    URL: https://serpapi.com/search
    Params:
      engine: "google_jobs"
      q: query (e.g. "Python Backend Engineer internship")
      location: location
      api_key: SERPAPI_KEY
      num: num_results
      gl: "in"
      hl: "en"
  
  Extract from response["jobs_results"]:
    For each job: title, company, location, description, url, source, posted_at,
    requirements (keyword extract), experience_level (infer)
  
  Deduplicate by title+company hash.
  Return list of cleaned job dicts.
  
  Error handling:
  - If SerpAPI returns error: log it, return empty list
  - If SERPAPI_KEY not set: return mock data (2-3 fake jobs) for development

def extract_skills_from_description(description: str) -> list[str]:
  Common skills to check: Python, JavaScript, TypeScript, React, Node.js, FastAPI,
  Django, Flask, SQL, PostgreSQL, MongoDB, Redis, Docker, Kubernetes, AWS, GCP, Azure,
  Git, REST API, GraphQL, Machine Learning, TensorFlow, PyTorch, Java, C++, Go, Rust,
  Spring Boot, Microservices, CI/CD, Linux, Agile, Scrum

def infer_source(url: str) -> str:
  linkedin / internshala / wellfound / naukri / other
```

### Step 3.5 — Semantic Search Tool
**Prompt for Cursor (open `/backend/tools/semantic_search.py`):**
```
Write a LangChain Tool for semantic job matching using Google Gemini embeddings and Supabase pgvector.

Requirements:
- from langchain_google_genai import GoogleGenerativeAIEmbeddings
- from backend.db.supabase_client import save_job_embedding, search_similar_jobs
- import os

IMPORTANT: Gemini text-embedding-004 produces 768-dim vectors (not 1536).
The Supabase schema must use vector(768).

def get_embeddings_model():
  return GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=os.getenv("GEMINI_API_KEY")
  )

@tool
def embed_and_store_job(job_id: str, job_text: str) -> bool:
  """Generate and store 768-dim embedding for a job listing using Gemini."""
  embedder = get_embeddings_model()
  embedding = embedder.embed_query(job_text)  # returns list of 768 floats
  save_job_embedding(job_id, embedding)
  return True

def create_job_embedding_text(job: dict) -> str:
  """Create a rich text representation of a job for embedding."""
  Return: f"Title: {title}\nCompany: {company}\nDescription: {description}\nRequirements: {requirements_text}\nSkills needed: {skills}"

@tool
def semantic_search_jobs(student_skills_text: str, top_k: int = 15, threshold: float = 0.6) -> list[dict]:
  """Find semantically similar jobs using Gemini vector similarity search."""
  embedder = get_embeddings_model()
  embedding = embedder.embed_query(student_skills_text)  # 768-dim
  return search_similar_jobs(embedding, threshold, top_k)

def create_student_skills_text(skill_graph: dict, career_goals: dict) -> str:
  """Create rich skills text for embedding from student profile."""
  skills_list = ", ".join([f"{skill} (level {score}/10)" for skill, score in skill_graph.items()])
  roles = ", ".join(career_goals.get("preferred_roles", []))
  Return: f"Skills: {skills_list}\nTarget roles: {roles}\nPreferences: {career_goals}"
```

### Step 3.6 — Interview Tool
**Prompt for Cursor (open `/backend/tools/interview_tool.py`):**
```
Write LangChain Tools for interview question generation and answer evaluation using Google Gemini.

Requirements:
- from langchain_google_genai import ChatGoogleGenerativeAI
- from langchain_core.output_parsers import JsonOutputParser
- import os

def get_llm(temperature=0.7):
  return ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=temperature
  )

@tool
def generate_interview_questions(
  student_profile: dict,
  job_description: str,
  question_type: str,
  num_questions: int = 5
) -> list[dict]:
  """Generate targeted interview questions based on type.
  question_type: 'hr' | 'technical' | 'system_design' | 'project'
  """
  
  llm = get_llm(temperature=0.7)
  
  Build type-specific prompts (same logic as before):
  HR: STAR method behavioral questions
  Technical: language/framework-specific coding + concepts
  System Design: architecture/scalability questions based on domain scores
  Project: deep dive into student's actual projects
  
  Include in prompt: "Return ONLY valid JSON array. No markdown backticks."
  Strip code fences before parsing.
  
  Return list of question dicts with: question, expected_answer, difficulty, topic, type, follow_ups

@tool
def evaluate_interview_answer(
  question: str,
  expected_answer: str,
  student_answer: str,
  question_type: str
) -> dict:
  """Evaluate a student's interview answer using Gemini AI."""
  
  llm = get_llm(temperature=0)
  
  Prompt: "You are an experienced interviewer. Evaluate this answer and return ONLY JSON (no markdown):
  {{
    'score': 0-10,
    'what_was_good': 'specific positive feedback',
    'what_to_improve': 'specific improvement advice',
    'model_answer': 'ideal answer for this question',
    'keywords_missed': ['important terms not mentioned']
  }}"
  
  Strip code fences, parse JSON, return dict.
```

---

## PHASE 4: AI AGENTS (GEMINI VERSIONS)

> **Global import change for ALL agents:**
> ```python
> # OLD (OpenAI)
> from langchain_openai import ChatOpenAI
> llm = ChatOpenAI(model="gpt-4o", temperature=0)
>
> # NEW (Gemini)
> from langchain_google_genai import ChatGoogleGenerativeAI
> import os
> llm = ChatGoogleGenerativeAI(
>     model="gemini-2.0-flash",
>     google_api_key=os.getenv("GEMINI_API_KEY"),
>     temperature=0
> )
> ```
> Always strip markdown code fences before calling `JsonOutputParser().parse(...)`:
> ```python
> raw = llm.invoke(prompt).content
> clean = raw.strip().strip("```json").strip("```").strip()
> result = JsonOutputParser().parse(clean)
> ```

### Step 4.1 — Profile Agent
**Prompt for Cursor (open `/backend/agents/profile_agent.py`):**
```
Write the Profile Analysis Agent as a LangGraph node using Google Gemini.

def profile_agent(state: AgentState) -> AgentState:
  """Parses resume, analyzes GitHub, builds skill graph using Gemini."""
  
  update_analysis_status(state["student_id"], "profile_agent", [], 10)
  
  Step 1: Parse resume
  from backend.tools.resume_parser import parse_resume_text
  parsed_resume = parse_resume_text.invoke({"resume_text": state["student_data"]["resume_text"]})
  
  Step 2: Analyze GitHub (if username provided)
  from backend.tools.github_tool import analyze_github_profile
  github_username = state["student_data"].get("github_username", "")
  github_result = {}
  if github_username:
    github_result = analyze_github_profile.invoke({"github_username": github_username})
  
  Step 3: Build comprehensive skill graph using Gemini
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  
  Build skill graph prompt (same structure as before):
  - Analyze parsed_resume skills + GitHub language scores
  - Return skill_graph as {"skill": score_1_to_10} for every skill found
  - Return domain_scores as {"backend": X, "frontend": X, "ml": X, "devops": X, "mobile": X}
  - Return profile_completeness 0-100
  - Return strength_analysis paragraph
  
  IMPORTANT: Tell Gemini: "Return ONLY valid JSON. No markdown. No backticks."
  Strip code fences before JsonOutputParser.
  
  Step 4: Save to Supabase (same as original)
  
  Step 5: Update state and return
  state["student_data"]["parsed_resume"] = parsed_resume
  state["student_data"]["github_result"] = github_result
  state["skill_graph"] = profile_result["skill_graph"]
  state["domain_scores"] = profile_result["domain_scores"]
```

### Step 4.2 — Job Match Agent
**Prompt for Cursor (open `/backend/agents/job_match_agent.py`):**
```
Write the Job Matching Agent as a LangGraph node using Google Gemini.

def job_match_agent(state: AgentState) -> AgentState:
  """Scrapes jobs, embeds them with Gemini, and scores matches."""
  
  update_analysis_status(state["student_id"], "job_match_agent", ["profile_agent"], 30)
  
  Step 1-3: Same as original (scrape SerpAPI, scrape multiple queries, deduplicate)
  
  Step 4: Save jobs and create Gemini embeddings
  from backend.tools.semantic_search import embed_and_store_job, create_job_embedding_text
  from backend.tools.job_scraper import scrape_jobs_serpapi
  
  saved_jobs = []
  for job in unique_jobs[:30]:
    saved = save_job(job)
    job_text = create_job_embedding_text(job)
    embed_and_store_job.invoke({"job_id": saved["id"], "job_text": job_text})
    saved_jobs.append(saved)
  
  Step 5: Semantic search with Gemini embeddings
  from backend.tools.semantic_search import semantic_search_jobs, create_student_skills_text
  skills_text = create_student_skills_text(state["skill_graph"], state["student_data"]["career_goals"])
  semantic_matches = semantic_search_jobs.invoke({"student_skills_text": skills_text, "top_k": 20})
  
  Step 6: Score matches with Gemini
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  
  For each of top 15 semantic matches:
    prompt = f"""Rate how well this student matches this job.
    Student Skills: {state["skill_graph"]}
    Student Goals: {state["student_data"]["career_goals"]}
    Job: {job["title"]} at {job["company"]}
    Description: {job["description"][:500]}
    
    Return ONLY this JSON (no markdown):
    {{
      "match_percentage": 0-100,
      "eligibility_notes": "why they qualify or not",
      "priority_rank": "high/medium/low",
      "missing_skills": ["skill1", "skill2"],
      "matching_skills": ["skill1", "skill2"]
    }}"""
    
    raw = llm.invoke(prompt).content
    clean = raw.strip().strip("```json").strip("```").strip()
    result = JsonOutputParser().parse(clean)
  
  Sort by match_percentage DESC.
  Update analysis status to 40%.
  Return updated state.
```

### Step 4.3 — ATS Resume Optimization Agent
**Prompt for Cursor (open `/backend/agents/ats_agent.py`):**
```
Write the ATS Resume Optimization Agent as a LangGraph node.
(Uses the ats_tool.py tools which already use Gemini — just call them.)

def ats_agent(state: AgentState) -> AgentState:
  """Optimizes resume for top matched jobs using ATS analysis via Gemini."""
  
  update_analysis_status(state["student_id"], "ats_agent", [...completed], 50)
  
  resume_text = state["student_data"]["resume_text"]
  top_jobs = state["matched_jobs"][:5]
  
  resume_versions = []
  all_missing_keywords = []
  
  for job in top_jobs:
    from backend.tools.ats_tool import analyze_ats_compatibility, generate_optimized_resume
    
    ats_result = analyze_ats_compatibility.invoke({
      "resume_text": resume_text,
      "job_description": job["description"],
      "job_title": job["title"],
      "company": job["company"]
    })
    
    optimized = generate_optimized_resume.invoke({
      "original_resume": resume_text,
      "job_description": job["description"],
      "ats_analysis": ats_result
    })
    
    version = { ...build version dict... }
    save_resume_version(state["student_id"], job["id"], version)
    resume_versions.append(version)
    all_missing_keywords.extend(ats_result.get("missing_keywords", []))
  
  from collections import Counter
  keyword_freq = Counter(all_missing_keywords)
  master_missing = [kw for kw, count in keyword_freq.most_common(10) if count >= 2]
  
  Return state with resume_versions updated.
```

### Step 4.4 — Skill Gap Agent
**Prompt for Cursor (open `/backend/agents/skill_gap_agent.py`):**
```
Write the Skill Gap Analysis Agent as a LangGraph node using Google Gemini.

def skill_gap_agent(state: AgentState) -> AgentState:
  """Identifies skill gaps and generates personalized learning roadmap using Gemini."""
  
  update_analysis_status(...)
  
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  
  Extract required skills from top 10 matched jobs (same logic as before).
  
  System context + user prompt (combined in single message for Gemini):
  "You are a senior technical career coach specialized in helping engineering students get placed.
  
  Perform a comprehensive skill gap analysis and create a learning roadmap.
  Return ONLY valid JSON (no markdown, no backticks):
  
  STUDENT CURRENT SKILLS (with proficiency 1-10):
  {state['skill_graph']}
  
  SKILLS REQUIRED BY TARGET JOBS:
  {list(all_required_skills)}
  
  TOP MATCHED JOBS:
  {[f'{j['title']} at {j['company']}' for j in state['matched_jobs'][:5]]}
  
  STUDENT CAREER GOALS:
  {state['student_data']['career_goals']}
  
  {{
    'critical_missing': [...],
    'nice_to_have': [...],
    'emerging_trends': [...],
    'learning_roadmap': [...],  // 12 weeks
    'weekly_time_required': X,
    'certifications': [...],
    'quick_skill_wins': [...],
    'summary': '...'
  }}"
  
  Strip markdown code fences before parsing.
  Save to Supabase and return updated state.
```

### Step 4.5 — Interview Preparation Agent
**Prompt for Cursor (open `/backend/agents/interview_agent.py`):**
```
Write the Interview Preparation Agent as a LangGraph node using Google Gemini.

def interview_agent(state: AgentState) -> AgentState:
  """Generates interview prep material using Gemini."""
  
  update_analysis_status(...)
  
  top_job = state["matched_jobs"][0] if state["matched_jobs"] else {}
  questions_bank = {}
  
  Step 1: Generate all question types
  from backend.tools.interview_tool import generate_interview_questions
  for q_type in ["hr", "technical", "system_design", "project"]:
    questions = generate_interview_questions.invoke({...})
    questions_bank[q_type] = questions
  
  Step 2: Calculate readiness scores using Gemini
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  
  scores_prompt = f"""Based on this student profile, estimate interview readiness.
  Skill Graph: {state["skill_graph"]}
  Skill Gaps: {state.get("skill_gaps", {}).get("critical_missing", [])}
  Domain Scores: {state.get("domain_scores", {})}
  Projects: {student_profile.get("projects", [])}
  
  Return ONLY this JSON (no markdown):
  {{
    "readiness_score": 0-100,
    "confidence_score": 0-100,
    "weak_areas": [...],
    "strong_areas": [...],
    "most_likely_questions": [...],
    "preparation_priority": [...]
  }}"""
  
  raw = llm.invoke(scores_prompt).content
  clean = raw.strip().strip("```json").strip("```").strip()
  scores = JsonOutputParser().parse(clean)
  
  Step 3: Save session to Supabase and return updated state.

Also write run_mock_interview() function (same structure as before, using Gemini evaluate_interview_answer tool).
```

### Step 4.6 — Referral Discovery Agent
**Prompt for Cursor (open `/backend/agents/referral_agent.py`):**
```
Write the Referral Discovery Agent as a LangGraph node using Google Gemini.

def referral_agent(state: AgentState) -> AgentState:
  """Generates personalized referral strategies using Gemini."""
  
  update_analysis_status(...)
  
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3
  )
  
  top_companies = [job["company"] for job in state["matched_jobs"][:8]]
  
  for company in set(top_companies[:6]):
    prompt = f"""Generate a referral networking strategy for this student targeting {company}.
    
    STUDENT PROFILE:
    Skills: {list(state["skill_graph"].keys())[:10]}
    Education: {state["student_data"].get("education", [{}])[0]}
    Projects: {[p["name"] for p in state["student_data"].get("projects", [])[:3]]}
    Target Role: {matching_job.get("title", "Software Engineer")}
    
    COMPANY: {company}
    
    Return ONLY this JSON (no markdown backticks):
    {{
      "company": "{company}",
      "target_role": "...",
      "connection_types": [...],
      "outreach_templates": {{...}},
      "referral_pathway": [...],
      "where_to_find_contacts": [...],
      "dos_and_donts": {{...}}
    }}"""
    
    raw = llm.invoke(prompt).content
    clean = raw.strip().strip("```json").strip("```").strip()
    result = JsonOutputParser().parse(clean)
    
    Save to referrals table in Supabase.
    referrals.append(result)
  
  Return updated state with referrals.
```

### Step 4.7 — Career Strategy Agent
**Prompt for Cursor (open `/backend/agents/career_strategy_agent.py`):**
```
Write the Career Strategy Agent as a LangGraph node using Google Gemini.

def career_strategy_agent(state: AgentState) -> AgentState:
  """Synthesizes all data using Gemini to create comprehensive placement strategy."""
  
  update_analysis_status(state["student_id"], "career_strategy_agent", [...all_previous], 85)
  
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  
  Build comprehensive prompt (same structure as before).
  Prepend to the prompt:
  "You are India's top placement advisor with 15 years of experience placing students 
  from top engineering colleges at FAANG, unicorn startups, and MNCs. 
  You give direct, honest, actionable advice.
  Return ONLY valid JSON — no markdown, no backticks, no preamble."
  
  Context includes: education, skill_graph, domain_scores, matched_jobs, skill_gaps, interview_readiness.
  
  Return JSON structure (same as before):
  {{
    "target_companies": [...10 companies...],
    "focus_recommendation": {{...}},
    "skill_roi": [...],
    "placement_probability": {{...}},
    "action_plan_90_days": [...],
    "red_flags": [...],
    "quick_wins": [...],
    "honest_assessment": "...",
    "predicted_package_range": {{...}}
  }}
  
  Strip code fences before parsing.
  Save to Supabase career_strategies table.
  Return updated state.
```

### Step 4.8 — Application Tracking Agent
**Prompt for Cursor (open `/backend/agents/tracking_agent.py`):**
```
Write the Application Tracking Agent as a LangGraph node using Google Gemini.

def tracking_agent(state: AgentState) -> AgentState:
  """Aggregates all data into a tracking dashboard. Final graph node."""
  
  update_analysis_status(state["student_id"], "tracking_agent", [...all_agents], 95)
  
  Steps 1-4: Read from Supabase, compute funnel, conversion rates, score summary (same as before)
  
  Step 5: Generate next actions using Gemini
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  
  Prompt: "Based on this student's current state (skill gaps, readiness, strategy), 
  list the top 5 priority actions for THIS WEEK.
  Return ONLY a JSON array (no markdown): [{action, priority, why, time_needed}]"
  
  Strip code fences before parsing.
  
  Steps 6-8: Create progress_timeline, mark analysis complete, return final state.
```

---

## PHASE 5: LANGGRAPH ORCHESTRATOR

### Step 5.1 — Build the Graph
**Prompt for Cursor (open `/backend/graph/placement_graph.py`):**
```
Build the complete LangGraph StateGraph for the Autonomous Placement Cell AI.
No model-specific imports needed here — all agents handle their own Gemini calls.

Requirements:
- from langgraph.graph import StateGraph, END, START
- from langgraph.checkpoint.memory import MemorySaver
- Import all 8 agent functions from backend.agents.*
- from backend.schemas.state import AgentState

def create_placement_graph():
  graph = StateGraph(AgentState)
  
  Add nodes (one per agent):
  profile_agent, job_match_agent, ats_agent, skill_gap_agent,
  interview_agent, referral_agent, career_strategy_agent, tracking_agent
  
  Sequential edges:
  START → profile_agent → job_match_agent → ats_agent → skill_gap_agent
       → interview_agent → referral_agent → career_strategy_agent → tracking_agent → END
  
  Conditional edge after profile_agent:
  def check_profile_complete(state: AgentState) -> str:
    if state.get("error") or not state.get("skill_graph"):
      return "error_handler"
    return "job_match_agent"
  
  Add error_handler node that logs error and ends gracefully.
  
  Compile with MemorySaver checkpointing.

placement_graph = create_placement_graph()

async def run_placement_analysis(student_id: str, student_data: dict) -> dict:
  initial_state = AgentState(
    student_id=student_id,
    student_data=student_data,
    skill_graph={}, domain_scores={}, job_listings=[], matched_jobs=[],
    resume_versions=[], skill_gaps={}, interview_prep={}, referrals=[],
    career_strategy={}, applications=[],
    analysis_status={"current_agent": "starting", "completed_agents": [], "percentage": 0},
    error=None, messages=[]
  )
  config = {"configurable": {"thread_id": student_id}}
  try:
    final_state = await placement_graph.ainvoke(initial_state, config)
    return {"success": True, "state": final_state}
  except Exception as e:
    mark_analysis_failed(student_id, str(e))
    return {"success": False, "error": str(e)}
```

---

## PHASE 6: FASTAPI BACKEND

### Step 6.1 — All API Routes
**Prompt for Cursor (open `/backend/api/routes.py`):**
```
Write all FastAPI route handlers for the Placement Cell AI API.

Import:
- FastAPI, APIRouter, BackgroundTasks, HTTPException, UploadFile, File
- All Pydantic schemas from backend.schemas.state
- All supabase_client functions
- run_placement_analysis from backend.graph.placement_graph
- run_mock_interview from backend.agents.interview_agent
- simulate_recruiter_review from backend.agents.recruiter_simulator
- asyncio, logging

router = APIRouter(prefix="/api")

POST /api/students → Create student, initialize analysis_status
POST /api/analyze/{student_id} → Start background analysis
GET /api/status/{student_id} → Poll progress
GET /api/profile/{student_id} → Full profile
GET /api/jobs/{student_id} → Matched jobs with filters
GET /api/resume/{student_id} → Resume versions
GET /api/skills/{student_id} → Skill gaps + roadmap
GET /api/interview/{student_id} → Interview questions + scores
POST /api/mock-interview/{student_id} → Submit mock answers
GET /api/referrals/{student_id} → Referral strategies
GET /api/strategy/{student_id} → Career strategy
GET /api/tracking/{student_id} → Application dashboard
PUT /api/application/{student_id} → Update application status
POST /api/upload-resume/{student_id} → Upload PDF resume
POST /api/recruiter-simulate/{student_id} → Recruiter simulation
GET /api/probability/{student_id} → Placement probability

Add 404/400/500 error handling on every endpoint.
```

### Step 6.2 — Main Application
**Prompt for Cursor (open `/backend/main.py`):**
```
Write the FastAPI main.py for the Placement Cell AI backend.

Requirements:
- from fastapi import FastAPI
- from fastapi.middleware.cors import CORSMiddleware
- from contextlib import asynccontextmanager
- from dotenv import load_dotenv
- import os, logging

load_dotenv()  # Must be first

@asynccontextmanager
async def lifespan(app: FastAPI):
  # Startup
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger("placement_cell")
  logger.info("Starting Placement Cell AI API (Gemini Edition)...")
  
  # Verify Supabase connection
  from backend.db.supabase_client import supabase_admin
  try:
    supabase_admin.table("students").select("count").execute()
    logger.info("✅ Supabase Cloud connected")
  except Exception as e:
    logger.error(f"❌ Supabase connection failed: {e}")
    raise
  
  # Verify Gemini API key (replaces OpenAI check)
  if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY not set")
  logger.info("✅ Gemini API key found")
  
  # Quick Gemini connectivity test
  try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    test_llm = ChatGoogleGenerativeAI(
      model="gemini-2.0-flash",
      google_api_key=os.getenv("GEMINI_API_KEY"),
      temperature=0
    )
    test_llm.invoke("Say OK")
    logger.info("✅ Gemini API connection verified")
  except Exception as e:
    logger.warning(f"⚠️ Gemini API test failed: {e}")
  
  yield
  logger.info("Shutting down Placement Cell AI API")

app = FastAPI(
  title="Placement Cell AI API (Gemini Edition)",
  description="Autonomous AI Placement Officer powered by Google Gemini",
  version="3.0.0",
  lifespan=lifespan
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

Include router from api/routes.py

@app.get("/health")
def health_check():
  return {
    "status": "healthy",
    "service": "Placement Cell AI",
    "version": "3.0.0",
    "ai_provider": "Google Gemini 2.0 Flash",
    "supabase": "connected"
  }

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## PHASE 7: FRONTEND
(No changes from v2 — the frontend only calls FastAPI, it never talks to Gemini directly.)

### Step 7.1–7.10 — All Frontend Pages
All frontend prompts remain the same as v2. The pages and hooks are model-agnostic.
Refer to v2 build guide for:
- 7.1 API Client Library (`api.ts`)
- 7.2 Zustand Store
- 7.3 App Router (`App.tsx`)
- 7.4 Onboarding Page
- 7.5 Dashboard Page
- 7.6 Jobs Page
- 7.7 Resume Optimizer Page
- 7.8 Interview Prep Page
- 7.9 Career Strategy Page
- 7.10 Application Tracker Page

---

## PHASE 8: ADVANCED FEATURES (GEMINI VERSIONS)

### Step 8.1 — AI Recruiter Simulator
**Prompt for Cursor (open `/backend/agents/recruiter_simulator.py`):**
```
Write the AI Recruiter Simulator as a standalone function using Google Gemini.

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
import os

def simulate_recruiter_review(student_profile: dict, job: dict) -> dict:
  """Simulate a real recruiter reviewing the candidate using Gemini."""
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.4
  )
  
  company = job.get("company", "a tech company")
  role = job.get("title", "Software Engineer")
  
  prompt = f"""You are a senior technical recruiter at {company} with 10 years experience, 
  currently hiring for {role}. Review this candidate with your honest professional lens.
  Return ONLY valid JSON (no markdown):
  
  CANDIDATE PROFILE:
  Education: {student_profile.get("education")}
  Skills: {student_profile.get("skill_graph")}
  Experience: {student_profile.get("experience")}
  Projects: {student_profile.get("projects")}
  GitHub Stats: {student_profile.get("github_result", {})}
  
  JOB REQUIREMENTS:
  {job.get("description", "")}
  Required Skills: {job.get("requirements", {})}
  
  {{
    "first_impression": "...",
    "would_shortlist": true/false,
    "shortlist_probability": 0-100,
    "shortlist_reason": "...",
    "resume_ranking": 1-10,
    "candidate_suitability": "...",
    "screening_questions": [...],
    "red_flags": [...],
    "green_flags": [...],
    "profile_improvements": [...],
    "comparable_profiles": "...",
    "your_gut_feeling": "..."
  }}"""
  
  raw = llm.invoke(prompt).content
  clean = raw.strip().strip("```json").strip("```").strip()
  return JsonOutputParser().parse(clean)
```

### Step 8.2 — Probability Predictor
```
(No AI model calls — purely mathematical computation.)
Same as v2: fetch data from Supabase, compute weighted score, return breakdown.
No Gemini changes needed here.
```

---

## PHASE 9: TESTING

### Step 9.1 — Integration Test
**Prompt for Cursor (open `/backend/tests/test_pipeline.py`):**
```
Write integration tests for the Gemini-powered Placement Cell AI pipeline.

Same structure as v2 but with these Gemini-specific additions:

Setup section should also verify GEMINI_API_KEY is loaded from .env.

Add this test:
def test_gemini_llm_connection():
  """Verify Gemini API key is valid and connection works."""
  from langchain_google_genai import ChatGoogleGenerativeAI
  import os
  from dotenv import load_dotenv
  load_dotenv()
  
  llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
  )
  response = llm.invoke("Return the single word: CONNECTED")
  assert "CONNECTED" in response.content or len(response.content) > 0

def test_gemini_embeddings():
  """Verify Gemini embeddings produce 768-dim vectors."""
  from langchain_google_genai import GoogleGenerativeAIEmbeddings
  import os
  
  embedder = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=os.getenv("GEMINI_API_KEY")
  )
  embedding = embedder.embed_query("Python developer with FastAPI experience")
  assert len(embedding) == 768, f"Expected 768 dims, got {len(embedding)}"
  assert all(isinstance(v, float) for v in embedding)

@pytest.mark.asyncio
async def test_full_pipeline():
  (Same sample resume and assertions as v2)
  
@pytest.mark.asyncio
async def test_supabase_connection():
  (Same as v2 — verify all 13 tables exist)

def test_ats_tool():
  (Same as v2 — test Gemini-powered ATS analysis)

Cleanup: delete test student after tests (teardown)
```

---

## PHASE 10: DEPLOYMENT — DETAILED

### Step 10.1 — Prepare Backend for Deployment

**Prompt for Cursor (open `/backend/requirements.txt`):**
```
Generate a clean production requirements.txt for the Placement Cell AI Gemini backend.

Include pinned versions:
langchain==0.2.16
langgraph==0.2.28
langchain-google-genai==1.0.10
langchain-community==0.2.16
langchain-core==0.2.38
google-generativeai==0.7.2
fastapi==0.115.0
uvicorn[standard]==0.30.6
gunicorn==22.0.0
supabase==2.7.4
python-dotenv==1.0.1
pydantic[email]==2.8.2
PyMuPDF==1.24.10
httpx==0.27.2
python-multipart==0.0.9

Create a separate requirements-dev.txt:
pytest==8.3.3
pytest-asyncio==0.24.0
black==24.8.0
ruff==0.6.8
```

**Prompt for Cursor (create `/backend/Dockerfile`):**
```
Write a production-ready Dockerfile for the FastAPI backend.

- Base: python:3.11-slim
- WORKDIR /app
- Install system deps: gcc, curl
- Copy requirements.txt first (cache optimization)
- pip install --no-cache-dir -r requirements.txt
- Copy rest of code
- Non-root user: useradd -m appuser, chown -R appuser /app, USER appuser
- Expose port 8000
- Health check: curl -f http://localhost:8000/health || exit 1
- CMD: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2

Do NOT include .env in Docker image.
Add .dockerignore excluding: .env, __pycache__, .venv, tests/, *.pyc
```

**Prompt for Cursor (create `/backend/render.yaml`):**
```
Write a render.yaml for deploying to Render.com using Gemini API.

services:
  - type: web
    name: placement-cell-api
    runtime: python
    region: singapore
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 2
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GEMINI_API_KEY          ← replaces OPENAI_API_KEY
        sync: false
      - key: GEMINI_MODEL
        value: gemini-2.0-flash
      - key: GEMINI_EMBEDDING_MODEL
        value: models/text-embedding-004
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SUPABASE_DB_URL
        sync: false
      - key: SERPAPI_KEY
        sync: false
      - key: GITHUB_TOKEN
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: CORS_ORIGINS
        sync: false
```

### Step 10.2 — Prepare Frontend for Deployment

**Prompt for Cursor (create `/frontend/vercel.json`):**
```
Write a vercel.json for deploying the Vite React frontend to Vercel.

{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{"source": "/(.*)", "destination": "/index.html"}],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {"key": "X-Frame-Options", "value": "DENY"},
        {"key": "X-Content-Type-Options", "value": "nosniff"}
      ]
    }
  ]
}

Note: VITE_API_BASE_URL must be set in Vercel dashboard to the Render backend URL.
```

### Step 10.3 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Autonomous Placement Cell AI (Gemini Edition)"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/placement-cell-ai.git
git push -u origin main
```

### Step 10.4 — Deploy Backend to Render

1. Go to https://render.com → Dashboard → **New +** → **Web Service**
2. Connect GitHub → Select your `placement-cell-ai` repository
3. Configure:
   - **Name:** `placement-cell-api`
   - **Region:** Singapore
   - **Branch:** main
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 2`
   - **Plan:** Free
4. Click **Advanced** → Add all environment variables one by one:
   - `GEMINI_API_KEY` → your actual Gemini key (starts with `AIza...`)
   - `GEMINI_MODEL` → `gemini-2.0-flash`
   - `GEMINI_EMBEDDING_MODEL` → `models/text-embedding-004`
   - `SUPABASE_URL` → your Supabase project URL
   - `SUPABASE_KEY` → your Supabase anon key
   - `SUPABASE_SERVICE_KEY` → your Supabase service role key
   - `SUPABASE_DB_URL` → your Supabase DB connection string
   - `SERPAPI_KEY` → your SerpAPI key
   - `GITHUB_TOKEN` → your GitHub token
   - `ENVIRONMENT` → `production`
   - `CORS_ORIGINS` → `http://localhost:5173` (update after Vercel deploy)
5. Click **Create Web Service** — wait 3-5 minutes
6. Test: open `https://placement-cell-api.onrender.com/health`
   - Should return: `{"status": "healthy", "ai_provider": "Google Gemini 2.0 Flash", ...}`

### Step 10.5 — Deploy Frontend to Vercel

1. Go to https://vercel.com → **Add New...** → **Project**
2. Import your `placement-cell-ai` GitHub repo
3. Configure:
   - **Framework Preset:** Vite (auto-detected)
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add Environment Variables:
   - `VITE_API_BASE_URL` → `https://placement-cell-api.onrender.com`
   - `VITE_SUPABASE_URL` → your Supabase URL
   - `VITE_SUPABASE_ANON_KEY` → your Supabase anon key
5. Click **Deploy** — wait 2 minutes

### Step 10.6 — Update CORS After Both Deploys

1. Go to Render Dashboard → Your service → **Environment**
2. Update `CORS_ORIGINS` to:
   ```
   http://localhost:5173,https://placement-cell-ai.vercel.app
   ```
3. Click **Save Changes** → Render redeploys automatically

### Step 10.7 — Verify Full Deployment

Open `https://placement-cell-ai.vercel.app` → go through onboarding → submit analysis.
Check Render logs — you should see agent progression and Gemini API calls.
Check Supabase Dashboard → Table Editor → verify rows are being created.

---

## GEMINI-SPECIFIC TROUBLESHOOTING

### Issue 1: JSON Parse Error from Gemini
**Symptom:** `JsonOutputParser` throws error even though the content looks like JSON.
**Cause:** Gemini sometimes wraps JSON in markdown code fences (\`\`\`json ... \`\`\`) despite instructions.
**Fix:** Always strip before parsing:
```python
raw = llm.invoke(prompt).content
clean = raw.strip()
if clean.startswith("```"):
    clean = clean.split("```")[1]
    if clean.startswith("json"):
        clean = clean[4:]
clean = clean.strip()
result = json.loads(clean)
```

### Issue 2: Rate Limit Hit (429 Error)
**Symptom:** `ResourceExhausted: 429 Quota exceeded`
**Cause:** Free tier limit is 15 RPM (requests per minute).
**Fix:** Add retry logic with exponential backoff:
```python
import time

def call_gemini_with_retry(llm, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                time.sleep(wait)
            else:
                raise
```

### Issue 3: Embedding Dimension Mismatch
**Symptom:** Supabase throws error on vector insert.
**Cause:** Schema has `vector(1536)` but Gemini produces 768-dim vectors.
**Fix:** Run this in Supabase SQL Editor to fix the columns:
```sql
ALTER TABLE job_embeddings ALTER COLUMN embedding TYPE vector(768);
ALTER TABLE student_embeddings ALTER COLUMN embedding TYPE vector(768);
-- Also recreate the match_jobs function with vector(768)
```

### Issue 4: `GEMINI_API_KEY` Not Loading in Tests
**Symptom:** `google.auth.exceptions.DefaultCredentialsError`
**Fix:** Always call `load_dotenv()` at the top of test files:
```python
from dotenv import load_dotenv
load_dotenv()  # must be before any Google imports
```

### Issue 5: Gemini Refuses to Answer
**Symptom:** Response is a refusal or safety block instead of JSON.
**Cause:** Gemini's safety filters may block prompts mentioning salary data, personal information, or competitive intelligence.
**Fix:** Rephrase prompts to be more academic/instructional in tone. Avoid words like "hack", "steal", "scrape aggressively".

---

## SUMMARY: ALL GEMINI CHANGES FROM v2

| Location | v2 (OpenAI) | v3 (Gemini) |
|---|---|---|
| `/backend/.env` | `OPENAI_API_KEY=sk-...` | `GEMINI_API_KEY=AIza...` |
| Python package | `langchain-openai` | `langchain-google-genai` |
| LLM class | `ChatOpenAI(model="gpt-4o")` | `ChatGoogleGenerativeAI(model="gemini-2.0-flash")` |
| Embeddings class | `OpenAIEmbeddings(model="text-embedding-3-small")` | `GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")` |
| Vector dimensions | `vector(1536)` | `vector(768)` |
| JSON parsing | Works directly | Strip code fences first |
| System prompts | `SystemMessage(...)` | Prepend to HumanMessage |
| Rate limit | 500 RPM (paid) | 15 RPM (free) — add retry |
| main.py check | `OPENAI_API_KEY` | `GEMINI_API_KEY` |
| render.yaml | `OPENAI_API_KEY` env var | `GEMINI_API_KEY` env var |

---

## SUMMARY: WHERE TO USE EACH TOOL

| Task | Use This Tool | Keyboard Shortcut |
|---|---|---|
| Generate a single file | Cursor Chat | Ctrl+L |
| Edit a specific block | Cursor Inline | Ctrl+K |
| Generate multiple related files | Trae Chat | Ask naturally |
| Debug a broken UI component | Antigravity | Connect to localhost:5173 |
| Fix layout/CSS issues | Antigravity | Screenshot → ask fix |
| Terminal commands | Cursor Terminal | Ctrl+` |

## BUILD ORDER — DO NOT SKIP

```
1. ✅ Phase 0: Accounts (including Google AI Studio) + setup + folder structure
2. ✅ Phase 1: Supabase schema with vector(768) — run SQL in dashboard
3. ✅ Phase 2: Pydantic schemas (state.py)
4. ✅ Phase 3: All 6 LangChain tools (Gemini versions)
5. ✅ Phase 4: Profile Agent ONLY → test manually in Python (verify Gemini call works)
6. ✅ Phase 5: LangGraph with just profile_agent → verify graph runs
7. ✅ Phase 4: Add Job Match Agent → test pipeline of 2 agents
8. ✅ Phase 6: FastAPI /analyze + /status + /profile routes only
9. ✅ Phase 7: Onboarding + Dashboard frontend only
10. ✅ Test end-to-end: onboarding → profile agent → dashboard shows data
11. ✅ Phase 4: Add remaining 6 agents one at a time, testing after each
12. ✅ Phase 6: Add remaining API routes
13. ✅ Phase 7: Add remaining frontend pages
14. ✅ Phase 8: Advanced features (recruiter sim, probability)
15. ✅ Phase 9: Run integration tests (including Gemini connection test)
16. ✅ Phase 10: Deploy (backend first, then frontend)
```

## QUICK REFERENCE: API ENDPOINTS

```
POST   /api/students                           Create student
POST   /api/analyze/{id}                       Start full analysis
GET    /api/status/{id}                        Poll agent progress
GET    /api/profile/{id}                       Get student profile
GET    /api/jobs/{id}?min_match=60             Get matched jobs
GET    /api/resume/{id}?job_id=xxx             Get optimized resume
GET    /api/skills/{id}                        Get skill gaps + roadmap
GET    /api/interview/{id}                     Get interview questions
POST   /api/mock-interview/{id}                Submit mock answers
GET    /api/referrals/{id}                     Get referral strategies
GET    /api/strategy/{id}                      Get career strategy
GET    /api/tracking/{id}                      Get application dashboard
PUT    /api/application/{id}                   Update application status
POST   /api/upload-resume/{id}                 Upload PDF resume
POST   /api/recruiter-simulate/{id}            Run recruiter simulation
GET    /api/probability/{id}                   Get placement probability
GET    /health                                 Health check
```

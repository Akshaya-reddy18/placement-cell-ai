# Autonomous Placement Cell AI

An autonomous AI system for managing placement activities, integrating with a React frontend and a FastAPI backend with Supabase for the database.

## Folder Structure
- `frontend/` - React frontend application
- `backend/` - FastAPI backend application
- `supabase/` - Local Supabase configurations and migrations

## Run the project

**Backend:**
```bash
cd "D:\Autonomous Placement Cell\placement-cell-ai"
uvicorn backend.main:app --reload
```

**Frontend:**
```bash
cd "D:\Autonomous Placement Cell\placement-cell-ai\frontend"
npm run dev
```

## API Routes

The backend uses FastAPI and is structured around multiple endpoints for onboarding, dashboard analytics, jobs, interviews, and more.

### Authentication & Core
- `POST /api/students` - Create a new student record
- `POST /api/onboarding` - Submit onboarding payload
- `GET /api/onboarding` - Get onboarding profile
- `GET /api/profile/{student_id}` - Get detailed student profile

### Dashboard & Status
- `GET /api/dashboard` - Get comprehensive dashboard metrics, deadlines, and charts
- `GET /api/status` - Get AI analysis pipeline status (current student)
- `GET /api/status/{student_id}` - Get AI analysis pipeline status (by ID)
- `POST /api/analyze/{student_id}` - Trigger full AI background analysis pipeline
- `GET /api/health` - Check backend health status

### Jobs & Applications
- `GET /api/jobs` - Fetch live real-time matched job listings
- `GET /api/jobs/{student_id}` - Get matched jobs
- `POST /api/apply/{student_id}/{job_id}` - Trigger a job application and add to tracker
- `GET /api/tracker` - Get application tracking dashboard (current student)
- `GET /api/tracking/{student_id}` - Get application tracking dashboard (by ID)
- `PUT /api/tracker/{application_id}` - Update tracking stage (e.g. from Applied to Interview)
- `PUT /api/application/{student_id}` - Create or update an application directly

### Resumes & Skills
- `GET /api/resume` - Get resume analysis and generated versions
- `GET /api/resume/{student_id}` - Get optimized resume versions
- `POST /api/upload-resume/{student_id}` - Upload a new resume PDF
- `GET /api/skills/{student_id}` - Get identified skill gaps and improvements

### Interviews & Career
- `GET /api/interview` - Get mock interview details and feedback
- `GET /api/interview/{student_id}` - Get mock interview feedback
- `POST /api/interview/chat` - Interact with the AI Mock Interviewer
- `GET /api/career` - Get comprehensive career strategy and roadmap
- `GET /api/strategy/{student_id}` - Get career strategy data
- `GET /api/referrals/{student_id}` - Fetch suggested network referrals
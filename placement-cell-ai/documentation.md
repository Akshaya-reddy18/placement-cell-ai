# Placement Cell AI Documentation

This document is a practical inventory of the project: what it does, what it uses, where the main entry points are, and which services, tables, and endpoints are part of the current codebase.

## Overview

Placement Cell AI is an AI-assisted placement and career support platform for students. The application has two main parts:

1. A FastAPI backend that runs the analysis pipeline, talks to Supabase, calls Google Gemini, and exposes JSON endpoints.
2. A React + Vite frontend that renders onboarding, dashboard, jobs, resume, interview, career, tracker, and settings screens.

The backend orchestration layer is built with LangGraph, and the LLM integration is built with LangChain + Google Gemini.

## Architecture

- Frontend: React 19, Vite, TypeScript, Tailwind, Zustand, React Query, React Router, Axios, Recharts, DnD Kit, Lucide, Base UI, Geist font.
- Backend: FastAPI, Uvicorn, Pydantic, Supabase Python client, LangChain, LangGraph, Google Gemini, PyMuPDF, httpx.
- Database: Supabase PostgreSQL with pgvector.

- External services: Google Gemini, Supabase, SerpAPI, GitHub API.

## Main Entry Points

- Backend application startup: backend/main.py
- Backend API routes: backend/api/routes.py
- Analysis graph: backend/graph/placement_graph.py
- Supabase access layer: backend/db/supabase_client.py
- Gemini helpers: backend/utils/ai_utils.py
- Frontend bootstrap: frontend/src/main.tsx
- Frontend app shell: frontend/src/App.tsx
- Frontend router: frontend/src/routes/AppRouter.tsx
- Frontend API client: frontend/src/lib/api.ts

## Backend Inventory

### Frontend Runtime Files

- backend/main.py: creates the FastAPI app, configures CORS, loads environment variables, verifies Supabase and Gemini connectivity, and starts Uvicorn when executed directly.
- backend/api/routes.py: defines the HTTP API for onboarding, dashboard, jobs, resume, interview, career, tracker, analysis status, profile, and uploads/chat flows.
- backend/graph/placement_graph.py: defines the LangGraph state machine and runs the placement analysis pipeline.
- backend/db/supabase_client.py: provides the Supabase client wrapper, local fallback client, CRUD helpers, semantic job search, and persistence helpers.
- backend/schemas/state.py: defines the typed state and Pydantic models used by the pipeline and API responses.
- backend/utils/ai_utils.py: centralizes Gemini model access, prompt helpers, JSON parsing helpers, tokenization, embeddings, and cosine similarity.

### Agents

The backend agent layer lives in backend/agents and is wired into the graph:

- backend/agents/profile_agent.py
- backend/agents/job_match_agent.py
- backend/agents/ats_agent.py
- backend/agents/skill_gap_agent.py
- backend/agents/interview_agent.py
- backend/agents/referral_agent.py
- backend/agents/career_strategy_agent.py
- backend/agents/tracking_agent.py
- backend/agents/recruiter_simulator.py
- backend/agents/probability_predictor.py

### Tools

The tool layer in backend/tools supports data extraction and external lookups:

- backend/tools/resume_parser.py: resume parsing with Gemini.
- backend/tools/github_tool.py: GitHub profile and repository analysis.
- backend/tools/ats_tool.py: ATS scoring and analysis helpers.
- backend/tools/job_scraper.py: live job search scraping with SerpAPI and fallback logic.
- backend/tools/semantic_search.py: semantic search helpers for jobs and embeddings.
- backend/tools/interview_tool.py: interview-generation helpers.

### API Surface

Current backend routes in backend/api/routes.py:

- POST /api/students
- POST /api/onboarding
- GET /api/onboarding
- GET /api/dashboard
- GET /api/status
- POST /api/analyze/{student_id}
- GET /api/status/{student_id}
- GET /api/profile/{student_id}
- GET /api/jobs/{student_id}
- GET /api/jobs
- GET /api/resume/{student_id}
- GET /api/resume
- GET /api/skills/{student_id}
- GET /api/interview/{student_id}
- GET /api/interview
- POST /api/interview/chat
- GET /api/referrals/{student_id}
- GET /api/strategy/{student_id}
- GET /api/career
- GET /api/tracking/{student_id}

### Backend Dependencies

The backend requirements file currently includes these runtime packages:

- annotated-types
- anyio
- attrs
- certifi
- charset-normalizer
- fastapi
- google-generativeai
- httpx
- langchain
- langchain-community
- langchain-core
- langchain-google-genai
- langgraph
- pydantic
- PyMuPDF
- python-dotenv
- python-multipart
- supabase
- uvicorn
- pytest
- pytest-asyncio

The backend also has a package.json for local CSS tooling, which is not the Python runtime:

- autoprefixer
- postcss
- tailwindcss

## Frontend Inventory

### Runtime Files

- frontend/src/main.tsx: mounts the React app and wraps it in React Query provider.
- frontend/src/App.tsx: forwards to the router.
- frontend/src/routes/AppRouter.tsx: defines public and protected routes.
- frontend/src/lib/api.ts: Axios client, request headers, mock fallback hooks, and endpoint wrappers.
- frontend/src/store/useStore.ts: global state store.
- frontend/src/data/mock.ts: mock data used by the demo mode.

### Pages

Frontend pages in frontend/src/pages:

- Onboarding.tsx
- Dashboard.tsx
- Jobs.tsx
- Resume.tsx
- Skills.tsx
- Interview.tsx
- Referrals.tsx
- Strategy.tsx
- Applications.tsx
- Career.tsx
- Tracker.tsx
- Settings.tsx

### Layout and Shared Components

Frontend components in frontend/src/components include:

- Layout components: AppShell, Header, Sidebar, ProtectedRoute
- Shared cards and UI: AIInsightCard, AnalyticsChart, EmptyState, InterviewCard, JobCard, LoadingState, MetricCard, MockInterviewModal, PageHeader, ProgressRing
- Core widgets: AgentStatus, JobCard, Sidebar, SkillBadge
- UI primitives under frontend/src/components/ui

### Frontend Dependencies

The frontend package.json uses:

- React
- React DOM
- React Router DOM
- React Query
- Axios
- Zustand
- Recharts
- DnD Kit core, sortable, utilities
- Lucide React
- Base UI
- Geist font source package
- shadcn
- clsx
- class-variance-authority
- tailwind-merge
- tw-animate-css

Frontend dev tools:

- Vite
- TypeScript
- ESLint
- @vitejs/plugin-react
- eslint-plugin-react-hooks
- eslint-plugin-react-refresh
- postcss
- autoprefixer
- tailwindcss

### Frontend Behavior Flags

- VITE_API_URL: backend base URL used by the Axios client.
- VITE_USE_MOCK: toggles demo mode versus live API mode.

## Database Schema

The schema is defined in backend/db/schema.sql. The project uses these tables:

- students
- student_profiles
- jobs
- job_embeddings
- student_embeddings
- job_matches
- resume_versions
- skill_gaps
- interview_sessions
- referrals
- career_strategies
- applications
- analysis_status

### Database Extensions and Indexes

- pgvector is enabled for similarity search.
- uuid-ossp is enabled for UUID support.
- Vector indexes are defined on job_embeddings and student_embeddings.
- Trigger-based updated_at maintenance exists for students, student_profiles, and skill_gaps.
- The match_jobs RPC function performs semantic job search over 768-dimensional embeddings.

## Environment Variables

Backend variables used in code:

- GOOGLE_API_KEY
- GEMINI_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- SUPABASE_ANON_KEY
- SERPAPI_KEY
- GITHUB_TOKEN
- CORS_ORIGINS

Frontend variables used in code:

- VITE_API_URL
- VITE_USE_MOCK

The project supports both GOOGLE_API_KEY and GEMINI_API_KEY for Gemini access. Supabase code prefers SUPABASE_SERVICE_KEY and falls back to SUPABASE_ANON_KEY when needed.

## External Services

- Google Gemini: LLM calls, interview generation, resume parsing, semantic helpers, and other AI features.
- Supabase: database, persistence, and pgvector-based search.
- SerpAPI: live job scraping.
- GitHub API: profile and repository-based analysis.

## Data Flow

1. A student submits onboarding data in the frontend.
2. The frontend sends the payload to the FastAPI backend.
3. The backend upserts the student into Supabase and initializes analysis status.
4. The placement graph runs through profile, job matching, ATS, skill gap, interview, referral, career strategy, and tracking stages.
5. The backend stores derived records in Supabase tables such as student_profiles, job_matches, resume_versions, skill_gaps, interview_sessions, referrals, career_strategies, and analysis_status.
6. The frontend reads dashboard, resume, interview, career, and tracker data from the API.

## Frontend Routing

- Public route: onboarding
- Protected routes: dashboard, jobs, resume, interview, career, tracker, settings
- Unknown routes redirect to dashboard

## Runtime Notes

- The backend loads environment variables from backend/.env.
- The frontend can run in demo mode when VITE_USE_MOCK is not false.
- The backend includes local fallback logic so the app can still run when Supabase credentials are missing, though full functionality depends on the configured services.
- Gemini embeddings are treated as 768-dimensional in the database schema.

## File Structure Summary

- backend: FastAPI app, agents, tools, graph, schemas, DB helpers, tests, and service integrations.
- frontend: React/Vite UI, pages, layouts, shared components, store, hooks, data, and API client.
- supabase: local Supabase configuration and snippets.
- projectGuide.md: setup and implementation guide for the full stack.
- README.md: short project summary.

## What This Document Covers

This file intentionally tracks the current codebase surface, including the app entry points, route handlers, schema tables, environment variables, and external integrations that the project uses today.

-- Enable pgvector extension for AI embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. students
CREATE TABLE IF NOT EXISTS public.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE, -- References auth.users(id) but can be loosely coupled
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    college TEXT,
    branch TEXT,
    graduation_year INTEGER,
    github_url TEXT,
    linkedin_url TEXT,
    resume_url TEXT,
    resume_text TEXT,
    career_goals JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 2. student_profiles
CREATE TABLE IF NOT EXISTS public.student_profiles (
    student_id UUID PRIMARY KEY REFERENCES public.students(id) ON DELETE CASCADE,
    skill_graph JSONB,
    career_profile JSONB,
    domains JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 3. jobs
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    source TEXT,
    url TEXT UNIQUE,
    description TEXT,
    requirements JSONB,
    location TEXT,
    experience_level TEXT,
    posted_at TEXT,
    is_active BOOLEAN DEFAULT true,
    work_mode TEXT,
    employment_type TEXT,
    company_type TEXT,
    industry TEXT,
    is_verified BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 4. job_embeddings
CREATE TABLE IF NOT EXISTS public.job_embeddings (
    job_id UUID PRIMARY KEY REFERENCES public.jobs(id) ON DELETE CASCADE,
    embedding vector(768)
);

-- 5. job_matches
CREATE TABLE IF NOT EXISTS public.job_matches (
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    match_percentage FLOAT,
    eligibility_notes TEXT,
    priority_rank TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    PRIMARY KEY (student_id, job_id)
);

-- 6. resume_versions
CREATE TABLE IF NOT EXISTS public.resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    ats_score FLOAT,
    missing_keywords JSONB,
    present_keywords JSONB,
    suggestions JSONB,
    optimized_resume_text TEXT,
    original_resume_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    UNIQUE(student_id, job_id)
);

-- 7. skill_gaps
CREATE TABLE IF NOT EXISTS public.skill_gaps (
    student_id UUID PRIMARY KEY REFERENCES public.students(id) ON DELETE CASCADE,
    critical_missing JSONB,
    nice_to_have JSONB,
    emerging_trends JSONB,
    learning_roadmap JSONB,
    weekly_plans JSONB,
    certifications JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 8. interview_sessions
CREATE TABLE IF NOT EXISTS public.interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE,
    session_type TEXT,
    questions_bank JSONB,
    mock_answers JSONB,
    feedback JSONB,
    confidence_score FLOAT,
    readiness_score FLOAT,
    weak_areas JSONB,
    strong_areas JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 9. career_strategies
CREATE TABLE IF NOT EXISTS public.career_strategies (
    student_id UUID PRIMARY KEY REFERENCES public.students(id) ON DELETE CASCADE,
    target_companies JSONB,
    focus_recommendation TEXT,
    placement_probability FLOAT,
    milestones JSONB,
    skill_gaps JSONB,
    learning_recommendations JSONB,
    market_insights JSONB,
    package_projection JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 10. analysis_status
CREATE TABLE IF NOT EXISTS public.analysis_status (
    student_id UUID PRIMARY KEY REFERENCES public.students(id) ON DELETE CASCADE,
    current_agent TEXT,
    completed_agents JSONB,
    percentage INTEGER,
    status TEXT,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 11. applications
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    company TEXT,
    role TEXT,
    stage TEXT,
    status TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- 12. referrals
CREATE TABLE IF NOT EXISTS public.referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE,
    company TEXT,
    target_role TEXT,
    connection_type TEXT,
    outreach_templates JSONB,
    referral_pathway TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Function to match jobs using vector similarity
DROP FUNCTION IF EXISTS public.match_jobs(vector, float, int);
CREATE OR REPLACE FUNCTION public.match_jobs (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  title text,
  company text,
  source text,
  url text,
  description text,
  requirements jsonb,
  location text,
  experience_level text,
  posted_at text,
  is_active boolean,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    j.id,
    j.title,
    j.company,
    j.source,
    j.url,
    j.description,
    j.requirements,
    j.location,
    j.experience_level,
    j.posted_at,
    j.is_active,
    1 - (je.embedding <=> query_embedding) AS similarity
  FROM jobs j
  JOIN job_embeddings je ON j.id = je.job_id
  WHERE 1 - (je.embedding <=> query_embedding) > match_threshold
  ORDER BY je.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

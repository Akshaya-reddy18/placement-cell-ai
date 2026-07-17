-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TABLE: students
CREATE TABLE students (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  email text UNIQUE NOT NULL,
  college text,
  branch text,
  graduation_year int,
  github_url text,
  linkedin_url text,
  resume_url text,
  resume_text text,
  career_goals jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- TABLE: student_profiles
CREATE TABLE student_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  skill_graph jsonb,
  career_profile jsonb,
  domain_scores jsonb,
  strength_analysis text,
  profile_completeness int DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- TABLE: jobs
CREATE TABLE jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  company text NOT NULL,
  source text,
  url text,
  description text,
  requirements jsonb,
  location text,
  experience_level text,
  posted_at timestamptz,
  scraped_at timestamptz DEFAULT now(),
  is_active boolean DEFAULT true
);

-- TABLE: job_embeddings
CREATE TABLE job_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid REFERENCES jobs(id) ON DELETE CASCADE,
  embedding vector(768),
  created_at timestamptz DEFAULT now()
);

-- TABLE: student_embeddings
CREATE TABLE student_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  embedding vector(768),
  created_at timestamptz DEFAULT now()
);

-- TABLE: job_matches
CREATE TABLE job_matches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  job_id uuid REFERENCES jobs(id) ON DELETE CASCADE,
  match_percentage numeric(5,2),
  eligibility_notes text,
  priority_rank text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(student_id, job_id)
);

-- TABLE: resume_versions
CREATE TABLE resume_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  job_id uuid REFERENCES jobs(id) ON DELETE CASCADE,
  ats_score numeric(5,2),
  missing_keywords jsonb,
  present_keywords jsonb,
  suggestions jsonb,
  optimized_resume_text text,
  original_resume_text text,
  created_at timestamptz DEFAULT now()
);

-- TABLE: skill_gaps
CREATE TABLE skill_gaps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  critical_missing jsonb,
  nice_to_have jsonb,
  emerging_trends jsonb,
  learning_roadmap jsonb,
  weekly_plans jsonb,
  certifications jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- TABLE: interview_sessions
CREATE TABLE interview_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  session_type text,
  questions_bank jsonb,
  mock_answers jsonb,
  feedback jsonb,
  confidence_score numeric(5,2),
  readiness_score numeric(5,2),
  weak_areas jsonb,
  strong_areas jsonb,
  created_at timestamptz DEFAULT now()
);

-- TABLE: referrals
CREATE TABLE referrals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  company text,
  target_role text,
  connection_type text,
  outreach_templates jsonb,
  referral_pathway jsonb,
  created_at timestamptz DEFAULT now()
);

-- TABLE: career_strategies
CREATE TABLE career_strategies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  target_companies jsonb,
  focus_recommendation text,
  skill_roi jsonb,
  placement_probability numeric(5,2),
  action_plan_90_days jsonb,
  red_flags jsonb,
  quick_wins jsonb,
  created_at timestamptz DEFAULT now()
);

-- TABLE: applications
CREATE TABLE applications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  job_id uuid REFERENCES jobs(id) ON DELETE CASCADE,
  status text DEFAULT 'applied',
  applied_at timestamptz DEFAULT now(),
  last_updated timestamptz DEFAULT now(),
  notes text,
  UNIQUE(student_id, job_id)
);

-- TABLE: analysis_status
CREATE TABLE analysis_status (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE UNIQUE,
  current_agent text,
  completed_agents jsonb DEFAULT '[]',
  percentage int DEFAULT 0,
  status text DEFAULT 'pending',
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz
);

-- Create indexes
CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_job_matches_student_id ON job_matches(student_id);
CREATE INDEX idx_job_matches_job_id ON job_matches(job_id);
CREATE INDEX idx_applications_student_id ON applications(student_id);
CREATE INDEX idx_applications_status ON applications(status);

-- Vector indexes (using ivfflat with vector_cosine_ops)
CREATE INDEX idx_job_embeddings_embedding ON job_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_student_embeddings_embedding ON student_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Trigger function for updating updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER trg_students_updated_at
  BEFORE UPDATE ON students
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_student_profiles_updated_at
  BEFORE UPDATE ON student_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_skill_gaps_updated_at
  BEFORE UPDATE ON skill_gaps
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- RPC Function for Semantic Job Search
CREATE OR REPLACE FUNCTION match_jobs(
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  job_id uuid,
  title text,
  company text,
  description text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    j.id AS job_id,
    j.title,
    j.company,
    j.description,
    (1 - (je.embedding <=> query_embedding))::float AS similarity
  FROM job_embeddings je
  JOIN jobs j ON je.job_id = j.id
  WHERE (1 - (je.embedding <=> query_embedding)) >= match_threshold
  ORDER BY je.embedding <=> query_embedding ASC
  LIMIT match_count;
END;
$$;

-- =================================================================================
-- 1. ADD USER_ID & ENFORCE UNIQUE MAPPING TO AUTH.USERS
-- =================================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'students' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE students ADD COLUMN user_id UUID UNIQUE REFERENCES auth.users(id);
    END IF;
END $$;


-- =================================================================================
-- 2. ENABLE RLS & CREATE POLICIES FOR CORE TABLES
-- =================================================================================

ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    -- JOBS: Globally readable, but managed by backend
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read jobs' AND tablename = 'jobs') THEN
        CREATE POLICY "Public read jobs" ON jobs FOR SELECT USING (true);
    END IF;

    -- STUDENTS: Users can only see/edit their own record via user_id
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own student record' AND tablename = 'students') THEN
        CREATE POLICY "Users can view own student record" ON students FOR SELECT USING (auth.uid() = user_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own student record' AND tablename = 'students') THEN
        CREATE POLICY "Users can update own student record" ON students FOR UPDATE USING (auth.uid() = user_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own student record' AND tablename = 'students') THEN
        CREATE POLICY "Users can insert own student record" ON students FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;

    -- STUDENT_PROFILES: Use a subquery to verify the student_id matches the student's user_id
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own profile' AND tablename = 'student_profiles') THEN
        CREATE POLICY "Users can view own profile" ON student_profiles FOR SELECT USING (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own profile' AND tablename = 'student_profiles') THEN
        CREATE POLICY "Users can update own profile" ON student_profiles FOR UPDATE USING (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can insert own profile' AND tablename = 'student_profiles') THEN
        CREATE POLICY "Users can insert own profile" ON student_profiles FOR INSERT WITH CHECK (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()));
    END IF;
END $$;


-- =================================================================================
-- 3. DYNAMIC RLS FOR ALL OTHER STUDENT-SPECIFIC TABLES
-- =================================================================================

-- Safely check if each table actually exists and has a 'student_id' column before applying RLS
DO $$ 
DECLARE
  t text;
  pol text;
  table_exists boolean;
  col_exists boolean;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'analysis_status', 
    'job_matches', 
    'resume_versions', 
    'skill_gaps', 
    'interview_sessions', 
    'referrals', 
    'career_strategies', 
    'applications',
    'student_embeddings'
  ])
  LOOP
    -- 1. Check if table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = t
    ) INTO table_exists;
    
    -- 2. Check if student_id column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = t AND column_name = 'student_id'
    ) INTO col_exists;

    IF table_exists AND col_exists THEN
        -- Enable RLS
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        
        -- Create View Policy
        pol := format('Users can view own %I', t);
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = pol AND tablename = t) THEN
            EXECUTE format('CREATE POLICY %I ON %I FOR SELECT USING (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()))', pol, t);
        END IF;
        
        -- Create Update Policy
        pol := format('Users can update own %I', t);
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = pol AND tablename = t) THEN
            EXECUTE format('CREATE POLICY %I ON %I FOR UPDATE USING (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()))', pol, t);
        END IF;
        
        -- Create Insert Policy
        pol := format('Users can insert own %I', t);
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = pol AND tablename = t) THEN
            EXECUTE format('CREATE POLICY %I ON %I FOR INSERT WITH CHECK (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()))', pol, t);
        END IF;

        -- Create Delete Policy
        pol := format('Users can delete own %I', t);
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = pol AND tablename = t) THEN
            EXECUTE format('CREATE POLICY %I ON %I FOR DELETE USING (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()))', pol, t);
        END IF;
    END IF;
  END LOOP;
END $$;

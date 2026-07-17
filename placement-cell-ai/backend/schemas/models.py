from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Dict, Any, Optional

class StudentInput(BaseModel):
    name: str = Field(..., min_length=1, description="Full name of the student")
    email: str = Field(..., description="Unique email address of the student")
    college: Optional[str] = Field(None, description="Name of the college")
    branch: Optional[str] = Field(None, description="Branch of study")
    graduation_year: Optional[int] = Field(None, description="Year of graduation")
    github_url: Optional[str] = Field(None, description="GitHub profile URL")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    resume_url: Optional[str] = Field(None, description="URL of the uploaded resume in Supabase Storage")
    resume_text: Optional[str] = Field(None, description="Extracted plain text of the resume")
    career_goals: Optional[Dict[str, Any]] = Field(
        None, 
        description="Career preferences: preferred_roles, target_companies, work_preference, location"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "college": "State Engineering College",
                "branch": "Computer Science & Engineering",
                "graduation_year": 2026,
                "github_url": "https://github.com/janedoe",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "resume_url": "https://supabase.co/storage/v1/object/public/resumes/jane_doe_resume.pdf",
                "resume_text": "Extracted resume content with experience in Python, Django, React...",
                "career_goals": {
                    "preferred_roles": ["Backend Engineer", "Software Engineer"],
                    "target_companies": ["Google", "Stripe", "PostHog"],
                    "work_preference": "remote",
                    "location": "San Francisco"
                }
            }
        }
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 2000 or v > 2100):
            raise ValueError("Graduation year must be between 2000 and 2100")
        return v

    @field_validator("github_url", "linkedin_url", "resume_url")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URLs must start with http:// or https://")
        return v


class JobListing(BaseModel):
    title: str = Field(..., min_length=1, description="Job title")
    company: str = Field(..., min_length=1, description="Hiring company name")
    source: Optional[str] = Field(None, description="Scraping source: linkedin, wellfound, internshala, etc.")
    url: Optional[str] = Field(None, description="Direct URL to apply or view job")
    description: Optional[str] = Field(None, description="Full job description text")
    requirements: Optional[Any] = Field(None, description="Extracted requirements list or JSON structure")
    location: Optional[str] = Field(None, description="Job location")
    experience_level: Optional[str] = Field(None, description="Experience level tier: intern, junior, mid, senior")
    posted_at: Optional[str] = Field(None, description="ISO-formatted posted date timestamp")
    is_active: bool = Field(True, description="Indicates if the job listing is open")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Software Engineer (Backend)",
                "company": "TechCorp Solutions",
                "source": "linkedin",
                "url": "https://linkedin.com/jobs/view/123456",
                "description": "We are seeking a backend engineer experienced in Python, PostgreSQL, and FastAPI.",
                "requirements": ["3+ years experience with Python", "Experience with AWS", "Knowledge of pgvector"],
                "location": "Bangalore, India",
                "experience_level": "mid",
                "posted_at": "2026-06-12T10:00:00Z",
                "is_active": True
            }
        }
    )

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_levels = {"intern", "junior", "mid", "senior"}
            if v.lower() not in valid_levels:
                raise ValueError(f"experience_level must be one of {valid_levels}")
            return v.lower()
        return v


class JobMatch(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    job_id: str = Field(..., description="UUID of the job")
    match_percentage: float = Field(..., description="AI matched percentage (0-100)")
    eligibility_notes: Optional[str] = Field(None, description="Notes on match matching / eligibility details")
    priority_rank: Optional[str] = Field(None, description="Match priority rank: high, medium, low")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "7a35368a-2c8b-4a57-b08e-b8ebae95b111",
                "job_id": "18f5262c-87d3-4813-8991-f92e35a16222",
                "match_percentage": 89.5,
                "eligibility_notes": "Strong alignment in Python & FastAPI. Missing AWS experience.",
                "priority_rank": "high"
            }
        }
    )

    @field_validator("match_percentage")
    @classmethod
    def validate_match_percentage(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError("Match percentage must be between 0 and 100")
        return v

    @field_validator("priority_rank")
    @classmethod
    def validate_priority_rank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_ranks = {"high", "medium", "low"}
            if v.lower() not in valid_ranks:
                raise ValueError(f"priority_rank must be one of {valid_ranks}")
            return v.lower()
        return v


class ResumeVersion(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    job_id: str = Field(..., description="UUID of the job that this resume version was tailored for")
    ats_score: float = Field(..., description="Estimated ATS matching score (0-100)")
    missing_keywords: Optional[List[str]] = Field(None, description="Keywords from job description missing in resume")
    present_keywords: Optional[List[str]] = Field(None, description="Matched keywords found in resume")
    suggestions: Optional[List[str]] = Field(None, description="Tailoring suggestions and actionable advice")
    optimized_resume_text: Optional[str] = Field(None, description="Tailored/optimized resume content markdown/text")
    original_resume_text: Optional[str] = Field(None, description="Original raw resume text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "7a35368a-2c8b-4a57-b08e-b8ebae95b111",
                "job_id": "18f5262c-87d3-4813-8991-f92e35a16222",
                "ats_score": 92.0,
                "missing_keywords": ["Docker", "Redis"],
                "present_keywords": ["Python", "FastAPI", "PostgreSQL"],
                "suggestions": ["Add Docker deployment experience", "Incorporate Redis caching project in Experience section"],
                "optimized_resume_text": "Jane Doe - Full Stack Developer\n- Experience with FastAPI, Python...",
                "original_resume_text": "Jane Doe - Resume..."
            }
        }
    )

    @field_validator("ats_score")
    @classmethod
    def validate_ats_score(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError("ATS score must be between 0 and 100")
        return v


class SkillGapReport(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    critical_missing: Optional[List[str]] = Field(None, description="Crucial missing skills for target roles")
    nice_to_have: Optional[List[str]] = Field(None, description="Optional skills that improve placement chances")
    emerging_trends: Optional[List[str]] = Field(None, description="Newer industry trends relevant to target roles")
    learning_roadmap: Optional[Dict[str, Any]] = Field(None, description="Detailed customized study roadmap structure")
    weekly_plans: Optional[List[Dict[str, Any]]] = Field(None, description="Week-by-week actionable steps")
    certifications: Optional[List[str]] = Field(None, description="Recommended certifications to pursue")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "7a35368a-2c8b-4a57-b08e-b8ebae95b111",
                "critical_missing": ["Docker", "Kubernetes", "System Design"],
                "nice_to_have": ["TypeScript", "Next.js"],
                "emerging_trends": ["Generative AI Agents", "RAG architectures"],
                "learning_roadmap": {
                    "phase_1": "Containerization fundamentals",
                    "phase_2": "Cloud deployments"
                },
                "weekly_plans": [
                    {"week": 1, "topic": "Docker basics, building images", "hours": 6},
                    {"week": 2, "topic": "Multi-container setup with Docker Compose", "hours": 8}
                ],
                "certifications": ["AWS Certified Cloud Practitioner", "Docker Certified Associate"]
            }
        }
    )


class InterviewQuestion(BaseModel):
    question: str = Field(..., description="The generated interview question text")
    expected_topics: Optional[List[str]] = Field(None, description="Keywords or conceptual areas expected in response")
    difficulty: Optional[str] = Field(None, description="Difficulty rating: easy, medium, hard")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How does PostgreSQL's indexing mechanism differ from MongoDB?",
                "expected_topics": ["B-Tree", "Document indexing", "Relational indexes", "Scale and performance"],
                "difficulty": "medium"
            }
        }
    )

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_difficulties = {"easy", "medium", "hard"}
            if v.lower() not in valid_difficulties:
                raise ValueError(f"difficulty must be one of {valid_difficulties}")
            return v.lower()
        return v


class InterviewFeedback(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    session_type: str = Field(..., description="Type of session: prep or mock")
    questions_bank: Optional[List[Dict[str, Any]]] = Field(None, description="Bank of questions selected for this session")
    mock_answers: Optional[List[Dict[str, Any]]] = Field(None, description="Candidate responses and transcripts")
    feedback: Optional[Dict[str, Any]] = Field(None, description="Detailed score evaluations and recommendations")
    confidence_score: float = Field(..., description="Estimated candidate confidence level (0-100)")
    readiness_score: float = Field(..., description="Estimated job readiness level (0-100)")
    weak_areas: Optional[List[str]] = Field(None, description="Concepts and areas needing improvement")
    strong_areas: Optional[List[str]] = Field(None, description="Topics where candidate demonstrated mastery")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "7a35368a-2c8b-4a57-b08e-b8ebae95b111",
                "session_type": "mock",
                "questions_bank": [
                    {"id": 1, "question": "Explain database normalization.", "difficulty": "medium"}
                ],
                "mock_answers": [
                    {"question_id": 1, "answer": "Normalization is the process of organizing database fields..."}
                ],
                "feedback": {
                    "technical_depth": "Great grasp of 1NF, 2NF, 3NF. Weak on BCNF details.",
                    "communication": "Fluent, structured thoughts."
                },
                "confidence_score": 82.5,
                "readiness_score": 78.0,
                "weak_areas": ["BCNF", "Indexing details"],
                "strong_areas": ["Database Normalization basics", "SQL joins"]
            }
        }
    )

    @field_validator("session_type")
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        valid_types = {"prep", "mock"}
        if v.lower() not in valid_types:
            raise ValueError(f"session_type must be one of {valid_types}")
        return v.lower()

    @field_validator("confidence_score", "readiness_score")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError("Scores must be between 0 and 100")
        return v


class CareerStrategy(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    target_companies: Optional[List[str]] = Field(None, description="Curated list of target employers")
    focus_recommendation: Optional[str] = Field(None, description="Primary focus: e.g., Backend, Frontend, Full Stack, Data Science")
    skill_roi: Optional[Dict[str, Any]] = Field(None, description="Skill value-to-effort calculation scores")
    placement_probability: float = Field(..., description="AI estimated probability of placement (0-100)")
    action_plan_90_days: Optional[Dict[str, Any]] = Field(None, description="Actionable 30-60-90 day milestone steps")
    red_flags: Optional[List[str]] = Field(None, description="Gaps or weaknesses that could block placement")
    quick_wins: Optional[List[str]] = Field(None, description="Low-hanging fruit actions to quickly improve profile")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "7a35368a-2c8b-4a57-b08e-b8ebae95b111",
                "target_companies": ["TCS", "Infosys", "Cognizant", "Stripe"],
                "focus_recommendation": "Backend Software Engineer",
                "skill_roi": {
                    "SQL": "High ROI / Low Effort",
                    "Kubernetes": "Medium ROI / High Effort"
                },
                "placement_probability": 85.0,
                "action_plan_90_days": {
                    "30_days": "Finish Docker tutorials and build 2 projects",
                    "60_days": "Mock interviews and start applying",
                    "90_days": "Salary negotiation and onboarding"
                },
                "red_flags": ["No public web projects", "Blank GitHub contribution graph"],
                "quick_wins": ["Upload Python project to GitHub", "Write a README for portfolio repo"]
            }
        }
    )

    @field_validator("placement_probability")
    @classmethod
    def validate_placement_probability(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError("Placement probability must be between 0 and 100")
        return v


class AnalysisStatusResponse(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    current_agent: Optional[str] = Field(None, description="Currently running LLM/AI workflow agent name")
    completed_agents: Optional[List[str]] = Field([], description="List of agent workflows completed successfully")
    percentage: int = Field(..., description="Overall analysis pipeline progress percentage (0-100)")
    status: str = Field(..., description="Pipeline execution state: pending, running, completed, failed")
    started_at: Optional[str] = Field(None, description="ISO timestamp for when the analysis started")
    completed_at: Optional[str] = Field(None, description="ISO timestamp for when the analysis finished")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "7a35368a-2c8b-4a57-b08e-b8ebae95b111",
                "current_agent": "ResumeOptimizerAgent",
                "completed_agents": ["StudentProfilerAgent", "JobMatcherAgent"],
                "percentage": 65,
                "status": "running",
                "started_at": "2026-06-12T11:00:00Z",
                "completed_at": None
            }
        }
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"pending", "running", "completed", "failed"}
        if v.lower() not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v.lower()

    @field_validator("percentage")
    @classmethod
    def validate_percentage(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

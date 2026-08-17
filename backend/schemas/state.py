from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

class AgentState(TypedDict):
    student_id: str
    student_data: dict
    skill_graph: dict
    domain_scores: dict
    job_listings: list[dict]
    matched_jobs: list[dict]
    resume_versions: list[dict]
    skill_gaps: dict
    interview_prep: dict
    referrals: list[dict]
    career_strategy: dict
    applications: list[dict]
    analysis_status: dict
    error: str | None
    messages: list[dict]

class StudentInput(BaseModel):
    name: str
    email: EmailStr
    college: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    career_goals: Dict[str, Any] = Field(default_factory=dict)
    resume_text: Optional[str] = None

class JobListing(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)

class JobMatch(BaseModel):
    job_id: str
    match_percentage: float
    eligibility_notes: str
    priority_rank: str
    missing_skills: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)

class ResumeVersion(BaseModel):
    job_id: str
    ats_score: float
    optimized_resume_text: str
    suggestions: List[str] = Field(default_factory=list)

class SkillGapReport(BaseModel):
    critical_missing: List[str]
    nice_to_have: List[str]
    learning_roadmap: List[Dict[str, Any]]
    certifications: List[str]

class InterviewQuestion(BaseModel):
    question: str
    expected_answer: str
    difficulty: str
    type: str

class InterviewFeedback(BaseModel):
    score: int
    what_was_good: str
    what_to_improve: str
    model_answer: str

class CareerStrategy(BaseModel):
    target_companies: List[str]
    placement_probability: float
    action_plan_90_days: List[str]
    quick_wins: List[str]

class AnalysisStatusResponse(BaseModel):
    student_id: str
    current_agent: str
    percentage: int
    status: str
    completed_agents: List[str] = Field(default_factory=list)

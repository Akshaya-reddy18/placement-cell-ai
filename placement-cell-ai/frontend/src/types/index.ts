export type AIStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed';

export interface CareerGoals {
  preferredRoles: string[];
  targetCompanies: string[];
  workPreference: string; // Keeping for backward compatibility
  locations: string[];
  workModes: string[];
  employmentTypes: string[];
  companyTypes: string[];
  requiredConstraints: string[];
  salaryExpectation?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  college: string;
  branch: string;
  graduationYear: number;
  skills: string[];
  targetCompanies: string[];
  careerGoals: CareerGoals;
  resumeFileName?: string;
  onboardingComplete: boolean;
}

export interface AIStatusState {
  currentAgent: string;
  percentage: number;
  status: AIStatus;
  completedAgents: string[];
  errorMessage?: string;
}

export interface DashboardMetrics {
  applications: number;
  resumeScore: number;
  interviewReadiness: number;
  placementProbability: number;
  placementReadiness: number;
}

export interface AIInsight {
  id: string;
  title: string;
  description: string;
  type: 'tip' | 'warning' | 'success' | 'action';
  createdAt: string;
}

export interface Deadline {
  id: string;
  title: string;
  company: string;
  dueDate: string;
  type: 'application' | 'interview' | 'assessment';
}

export interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string;
  salary?: string;
  matchPercentage: number;
  matchReason?: string;
  requirements: string[];
  description: string;
  priority: 'high' | 'medium' | 'low';
  postedAt: string;
  source: string;
  url?: string;
  job_url?: string;
  apply_url?: string;
  work_mode?: string;
  employment_type?: string;
  company_type?: string;
  industry?: string;
  is_verified?: boolean;
}

export interface JobFilters {
  search: string;
  roles: string[];
  companies: string[];
  locations: string[];
  workModes: string[];
  employmentTypes: string[];
  companyTypes: string[];
  salaryMin: number;
  skills: string[];
}

export interface ResumeScores {
  ats: number;
  keyword: number;
  formatting: number;
  impact: number;
  overall: number;
}

export interface ResumeAnalysis {
  scores: ResumeScores;
  missingKeywords: string[];
  presentKeywords: string[];
  suggestions: string[];
  optimizedSummary: string;
  originalExcerpt: string;
  optimizedExcerpt: string;
  checklist: { id: string; label: string; done: boolean }[];
}

export interface InterviewQuestion {
  id: string;
  question: string;
  type: 'hr' | 'technical' | 'system_design' | 'project';
  difficulty: 'easy' | 'medium' | 'hard';
  topic: string;
}

export interface MockSession {
  id: string;
  title: string;
  date: string;
  score: number;
  questionsCount: number;
}

export interface InterviewData {
  readinessScore: number;
  confidenceScore: number;
  technicalQuestions: InterviewQuestion[];
  behavioralQuestions: InterviewQuestion[];
  mockSessions: MockSession[];
  weakAreas: string[];
  strongAreas: string[];
  feedback: string;
}

export interface CareerMilestone {
  id: string;
  title: string;
  description: string;
  quarter: string;
  status: 'completed' | 'in_progress' | 'upcoming';
}

export interface SkillGapItem {
  skill: string;
  priority: 'critical' | 'nice_to_have';
  marketDemand: number;
}

export interface CareerData {
  focusRecommendation: string;
  placementProbability: number;
  targetCompanies: string[];
  milestones: CareerMilestone[];
  skillGaps: SkillGapItem[];
  learningRecommendations: string[];
  marketInsights: { skill: string; demand: number; growth: number }[];
  packageProjection: { min: number; max: number };
}

export type ApplicationStage =
  | 'wishlist'
  | 'applied'
  | 'oa'
  | 'interview'
  | 'offer'
  | 'rejected';

export interface ApplicationCard {
  id: string;
  company: string;
  role: string;
  stage: ApplicationStage;
  date: string;
  priority: 'high' | 'medium' | 'low';
  notes?: string;
}

export interface TrackerAnalytics {
  byStage: { stage: string; count: number }[];
  conversionRates: {
    applyToOa: number;
    oaToInterview: number;
    interviewToOffer: number;
  };
}

export interface TrackerData {
  applications: ApplicationCard[];
  analytics: TrackerAnalytics;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  insights: AIInsight[];
  deadlines: Deadline[];
  recommendedJobs: JobListing[];
  chartData: { name: string; applications: number; interviews: number }[];
  readinessBreakdown: { name: string; value: number }[];
}

export interface OnboardingPayload {
  name: string;
  email: string;
  college: string;
  branch: string;
  graduationYear: number;
  skills: string[];
  targetCompanies: string[];
  careerGoals: CareerGoals;
  resumeFileName?: string;
}

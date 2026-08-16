import type {
  ApplicationCard,
  CareerData,
  DashboardData,
  InterviewData,
  JobListing,
  ResumeAnalysis,
  TrackerData,
  UserProfile,
} from '@/types';

export const mockUser: UserProfile = {
  id: 'stu-001',
  name: 'Priya Sharma',
  email: 'priya.sharma@college.edu',
  college: 'IIT Delhi',
  branch: 'Computer Science',
  graduationYear: 2026,
  skills: ['Python', 'React', 'TypeScript', 'PostgreSQL', 'FastAPI', 'Docker'],
  targetCompanies: ['Google', 'Stripe', 'Razorpay', 'Postman', 'Atlassian'],
  careerGoals: {
    preferredRoles: ['Backend Engineer', 'Full Stack Engineer'],
    targetCompanies: ['Google', 'Stripe', 'Razorpay'],
    workPreference: 'hybrid',
    location: 'Bangalore',
    salaryExpectation: '12-18 LPA',
  },
  resumeFileName: 'priya_sharma_resume.pdf',
  onboardingComplete: true,
};

export const mockDashboard: DashboardData = {
  metrics: {
    applications: 14,
    resumeScore: 82,
    interviewReadiness: 71,
    placementProbability: 78,
    placementReadiness: 74,
  },
  insights: [
    {
      id: '1',
      title: 'Add Docker to resume',
      description: '3 of your top matched jobs list containerization. Adding Docker could raise ATS score by ~8%.',
      type: 'action',
      createdAt: '2026-06-10',
    },
    {
      id: '2',
      title: 'Strong Python alignment',
      description: 'Your skill graph shows 9/10 in Python — matches 12 active backend roles in your pipeline.',
      type: 'success',
      createdAt: '2026-06-09',
    },
    {
      id: '3',
      title: 'Mock interview gap',
      description: 'System design readiness is below target. Schedule 2 mock sessions this week.',
      type: 'warning',
      createdAt: '2026-06-08',
    },
  ],
  deadlines: [
    { id: '1', title: 'Application deadline', company: 'Razorpay', dueDate: '2026-06-15', type: 'application' },
    { id: '2', title: 'Technical interview', company: 'Postman', dueDate: '2026-06-18', type: 'interview' },
    { id: '3', title: 'Online assessment', company: 'Stripe', dueDate: '2026-06-20', type: 'assessment' },
  ],
  recommendedJobs: [],
  chartData: [
    { name: 'Jan', applications: 2, interviews: 0 },
    { name: 'Feb', applications: 4, interviews: 1 },
    { name: 'Mar', applications: 6, interviews: 2 },
    { name: 'Apr', applications: 8, interviews: 3 },
    { name: 'May', applications: 11, interviews: 4 },
    { name: 'Jun', applications: 14, interviews: 5 },
  ],
  readinessBreakdown: [
    { name: 'Technical', value: 78 },
    { name: 'Resume', value: 82 },
    { name: 'Behavioral', value: 68 },
    { name: 'System Design', value: 55 },
  ],
};

export const mockJobs: JobListing[] = [
  {
    id: 'job-1',
    title: 'Backend Engineer Intern',
    company: 'Razorpay',
    location: 'Bangalore',
    salary: '₹40k/month',
    matchPercentage: 91,
    requirements: ['Python', 'FastAPI', 'PostgreSQL', 'Redis'],
    description: 'Build payment infrastructure APIs serving millions of transactions daily.',
    priority: 'high',
    postedAt: '2 days ago',
    source: 'LinkedIn',
  },
  {
    id: 'job-2',
    title: 'Software Engineer — New Grad',
    company: 'Postman',
    location: 'Bangalore',
    salary: '14-18 LPA',
    matchPercentage: 87,
    requirements: ['TypeScript', 'Node.js', 'React', 'REST APIs'],
    description: 'Join the API platform team building developer tools used globally.',
    priority: 'high',
    postedAt: '3 days ago',
    source: 'Wellfound',
  },
  {
    id: 'job-3',
    title: 'Full Stack Developer',
    company: 'Freshworks',
    location: 'Chennai',
    salary: '10-14 LPA',
    matchPercentage: 79,
    requirements: ['React', 'Python', 'SQL', 'AWS'],
    description: 'Develop customer-facing SaaS features with a focus on performance.',
    priority: 'medium',
    postedAt: '1 week ago',
    source: 'Naukri',
  },
  {
    id: 'job-4',
    title: 'Backend Developer',
    company: 'Swiggy',
    location: 'Bangalore',
    salary: '12-16 LPA',
    matchPercentage: 76,
    requirements: ['Java', 'Spring Boot', 'Microservices', 'Kafka'],
    description: 'Scale order management systems for peak traffic events.',
    priority: 'medium',
    postedAt: '5 days ago',
    source: 'LinkedIn',
  },
  {
    id: 'job-5',
    title: 'Platform Engineer',
    company: 'Atlassian',
    location: 'Remote — India',
    salary: '18-24 LPA',
    matchPercentage: 72,
    requirements: ['Go', 'Kubernetes', 'Docker', 'CI/CD'],
    description: 'Improve developer platform reliability and deployment pipelines.',
    priority: 'medium',
    postedAt: '4 days ago',
    source: 'LinkedIn',
  },
  {
    id: 'job-6',
    title: 'SDE I — Backend',
    company: 'Amazon',
    location: 'Hyderabad',
    salary: '16-22 LPA',
    matchPercentage: 68,
    requirements: ['Java', 'Data Structures', 'System Design', 'AWS'],
    description: 'Design and implement scalable backend services for retail systems.',
    priority: 'low',
    postedAt: '1 week ago',
    source: 'Amazon Jobs',
  },
];

mockDashboard.recommendedJobs = mockJobs.slice(0, 3);

export const mockResume: ResumeAnalysis = {
  scores: { ats: 82, keyword: 74, formatting: 88, impact: 71, overall: 79 },
  missingKeywords: ['Docker', 'Kubernetes', 'Redis', 'CI/CD', 'Microservices'],
  presentKeywords: ['Python', 'React', 'PostgreSQL', 'FastAPI', 'REST API', 'Git'],
  suggestions: [
    'Quantify project impact with metrics (e.g., "reduced latency by 40%")',
    'Add Docker deployment experience from your capstone project',
    'Include Redis caching in your backend project description',
    'Align skills section order with job description priority',
  ],
  optimizedSummary:
    'Backend-focused CS student with production experience in Python/FastAPI and React. Built scalable REST APIs handling 10K+ daily requests with PostgreSQL and Redis caching.',
  originalExcerpt:
    'Computer Science student passionate about building web applications. Experienced with Python, React, and databases.',
  optimizedExcerpt:
    'Backend Engineer (Python/FastAPI) with hands-on experience building REST APIs, PostgreSQL data models, and React dashboards. Deployed services with Docker on AWS.',
  checklist: [
    { id: '1', label: 'Add quantified achievements', done: false },
    { id: '2', label: 'Include Docker in skills', done: false },
    { id: '3', label: 'Match keywords to top job', done: true },
    { id: '4', label: 'Fix section headings for ATS', done: true },
    { id: '5', label: 'Add Redis to project stack', done: false },
  ],
};

export const mockInterview: InterviewData = {
  readinessScore: 71,
  confidenceScore: 68,
  technicalQuestions: [
    { id: 't1', question: 'Explain how you would design a rate limiter for an API.', type: 'technical', difficulty: 'medium', topic: 'System Design' },
    { id: 't2', question: 'What is the difference between SQL and NoSQL databases?', type: 'technical', difficulty: 'easy', topic: 'Databases' },
    { id: 't3', question: 'How does FastAPI dependency injection work?', type: 'technical', difficulty: 'medium', topic: 'Python' },
  ],
  behavioralQuestions: [
    { id: 'b1', question: 'Tell me about a time you resolved a conflict in a team project.', type: 'hr', difficulty: 'medium', topic: 'Teamwork' },
    { id: 'b2', question: 'Describe a situation where you had to learn a technology quickly.', type: 'hr', difficulty: 'easy', topic: 'Adaptability' },
  ],
  mockSessions: [
    { id: 'm1', title: 'Backend Technical Round', date: '2026-06-05', score: 72, questionsCount: 8 },
    { id: 'm2', title: 'HR Behavioral Round', date: '2026-06-01', score: 65, questionsCount: 6 },
  ],
  weakAreas: ['System Design', 'Distributed Systems', 'Behavioral STAR format'],
  strongAreas: ['Python', 'REST APIs', 'Database Design'],
  feedback: 'Strong technical fundamentals. Focus on structuring behavioral answers using STAR and practice system design for scale.',
};

export const mockCareer: CareerData = {
  focusRecommendation: 'Backend Software Engineer',
  placementProbability: 78,
  targetCompanies: ['Razorpay', 'Postman', 'Stripe', 'Google', 'Atlassian', 'Freshworks', 'Swiggy', 'Amazon', 'Microsoft', 'Flipkart'],
  milestones: [
    { id: 'm1', title: 'Complete Docker & K8s basics', description: 'Finish containerization course and deploy one project', quarter: 'Q1 2026', status: 'completed' },
    { id: 'm2', title: 'Apply to 20 target roles', description: 'Focus on backend roles in Bangalore', quarter: 'Q2 2026', status: 'in_progress' },
    { id: 'm3', title: '5 mock interviews', description: 'Mix of technical and behavioral', quarter: 'Q2 2026', status: 'in_progress' },
    { id: 'm4', title: 'System design certification', description: 'Complete structured system design prep', quarter: 'Q3 2026', status: 'upcoming' },
    { id: 'm5', title: 'Final placement', description: 'Secure offer from target company', quarter: 'Q4 2026', status: 'upcoming' },
  ],
  skillGaps: [
    { skill: 'System Design', priority: 'critical', marketDemand: 95 },
    { skill: 'Docker', priority: 'critical', marketDemand: 88 },
    { skill: 'Kubernetes', priority: 'nice_to_have', marketDemand: 82 },
    { skill: 'Redis', priority: 'critical', marketDemand: 76 },
  ],
  learningRecommendations: [
    'Complete 12-week backend roadmap — Week 3: Docker fundamentals',
    'Practice 2 system design problems per week',
    'Add one production-grade project to GitHub with README',
  ],
  marketInsights: [
    { skill: 'Python', demand: 92, growth: 8 },
    { skill: 'System Design', demand: 95, growth: 15 },
    { skill: 'Docker', demand: 88, growth: 12 },
    { skill: 'React', demand: 85, growth: 5 },
    { skill: 'Kubernetes', demand: 82, growth: 18 },
  ],
  packageProjection: { min: 12, max: 18 },
};

export const mockApplications: ApplicationCard[] = [
  { id: 'a1', company: 'Razorpay', role: 'Backend Engineer Intern', stage: 'interview', date: '2026-06-01', priority: 'high' },
  { id: 'a2', company: 'Postman', role: 'Software Engineer', stage: 'oa', date: '2026-06-03', priority: 'high' },
  { id: 'a3', company: 'Stripe', role: 'Backend Intern', stage: 'applied', date: '2026-06-05', priority: 'high' },
  { id: 'a4', company: 'Google', role: 'SWE New Grad', stage: 'wishlist', date: '2026-06-06', priority: 'medium' },
  { id: 'a5', company: 'Freshworks', role: 'Full Stack Dev', stage: 'applied', date: '2026-05-28', priority: 'medium' },
  { id: 'a6', company: 'Swiggy', role: 'Backend Developer', stage: 'rejected', date: '2026-05-15', priority: 'low' },
  { id: 'a7', company: 'Atlassian', role: 'Platform Engineer', stage: 'wishlist', date: '2026-06-07', priority: 'medium' },
  { id: 'a8', company: 'Microsoft', role: 'SDE', stage: 'offer', date: '2026-05-20', priority: 'high', notes: 'Verbal offer — negotiating' },
];

export const mockTracker: TrackerData = {
  applications: mockApplications,
  analytics: {
    byStage: [
      { stage: 'Wishlist', count: 2 },
      { stage: 'Applied', count: 2 },
      { stage: 'OA', count: 1 },
      { stage: 'Interview', count: 1 },
      { stage: 'Offer', count: 1 },
      { stage: 'Rejected', count: 1 },
    ],
    conversionRates: {
      applyToOa: 50,
      oaToInterview: 100,
      interviewToOffer: 100,
    },
  },
};

export const mockAIStatus = {
  currentAgent: 'career_strategy_agent',
  percentage: 100,
  status: 'completed' as const,
  completedAgents: ['profile_agent', 'job_match_agent', 'ats_agent', 'skill_gap_agent', 'interview_agent', 'career_strategy_agent'],
};

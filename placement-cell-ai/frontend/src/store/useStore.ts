import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { mockAIStatus } from '@/data/mock';
import type {
  AIStatusState,
  ApplicationCard,
  CareerData,
  DashboardData,
  InterviewData,
  JobFilters,
  JobListing,
  ResumeAnalysis,
  TrackerData,
  UserProfile,
} from '@/types';

interface UserSlice {
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;
  completeOnboarding: (user: UserProfile) => void;
}

interface AISlice {
  aiStatus: AIStatusState;
  setAIStatus: (status: Partial<AIStatusState>) => void;
}

interface DashboardSlice {
  dashboard: DashboardData | null;
  setDashboard: (data: DashboardData) => void;
}

interface JobsSlice {
  jobs: JobListing[];
  jobFilters: JobFilters;
  setJobs: (jobs: JobListing[]) => void;
  setJobFilters: (filters: Partial<JobFilters>) => void;
}

interface ResumeSlice {
  resume: ResumeAnalysis | null;
  setResume: (data: ResumeAnalysis) => void;
}

interface InterviewSlice {
  interview: InterviewData | null;
  setInterview: (data: InterviewData) => void;
}

interface CareerSlice {
  career: CareerData | null;
  setCareer: (data: CareerData) => void;
}

export type AppStore = UserSlice &
  AISlice &
  DashboardSlice &
  JobsSlice &
  ResumeSlice &
  InterviewSlice &
  CareerSlice;

const defaultFilters: JobFilters = {
  search: '',
  roles: [],
  companies: [],
  locations: [],
  workModes: [],
  employmentTypes: [],
  companyTypes: [],
  salaryMin: 0,
  skills: [],
};

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      user: null,
      setUser: (user) => set({ user }),
      completeOnboarding: (user) =>
        set({ user: { ...user, onboardingComplete: true } }),

      aiStatus: mockAIStatus,
      setAIStatus: (status) =>
        set({ aiStatus: { ...get().aiStatus, ...status } }),

      dashboard: null,
      setDashboard: (dashboard) => set({ dashboard }),

      jobs: [],
      jobFilters: defaultFilters,
      setJobs: (jobs) => set({ jobs }),
      setJobFilters: (filters) =>
        set({ jobFilters: { ...get().jobFilters, ...filters } }),

      resume: null,
      setResume: (resume) => set({ resume }),

      interview: null,
      setInterview: (interview) => set({ interview }),

      career: null,
      setCareer: (career) => set({ career }),

    }),
    {
      name: 'placement-cell-store-v2',
      partialize: (state) => ({
        // user: state.user, // Do not keep logged in by default
        aiStatus: state.aiStatus,
      }),
    },
  ),
);

export const useUser = () => useAppStore((s) => s.user);
export const useIsOnboarded = () => useAppStore((s) => s.user?.onboardingComplete ?? false);

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import {
  mockAIStatus,
  mockCareer,
  mockDashboard,
  mockInterview,
  mockJobs,
  mockResume,
  mockTracker,
  mockUser,
} from '@/data/mock';
import type {
  CareerData,
  DashboardData,
  InterviewData,
  JobListing,
  OnboardingPayload,
  ResumeAnalysis,
  TrackerData,
  UserProfile,
} from '@/types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function withMockFallback<T>(fetcher: () => Promise<T>, fallback: T): Promise<T> {
  const isGuest = localStorage.getItem('pc_token') === 'guest_token';
  if (USE_MOCK || isGuest) {
    await delay(500);
    return fallback;
  }
  // Remove silent fallback so real API errors bubble up to the UI
  return await fetcher();
}

import { supabase } from '@/lib/supabase';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  let token = localStorage.getItem('pc_token');

  // If we have an active Supabase session, use its fresh access token
  if (token && token !== 'guest_token') {
    try {
      const { data } = await supabase.auth.getSession();
      if (data?.session?.access_token) {
        token = data.session.access_token;
        localStorage.setItem('pc_token', token);
      }
    } catch {
      // ignore
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const studentId = localStorage.getItem('pc_student_id');
  if (studentId) {
    config.headers['X-Student-Id'] = studentId;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string; detail?: string }>) => {
    const detail = error.response?.data?.detail;
    if (error.response?.status === 401 && detail && (detail.toLowerCase().includes('token is expired') || detail.toLowerCase().includes('invalid jwt'))) {
      localStorage.removeItem('pc_token');
      localStorage.removeItem('pc_student_id');
    }
    const message = error.response?.data?.detail ?? error.response?.data?.message ?? error.message ?? 'Request failed';
    return Promise.reject(new Error(message));
  },
);

export const api = {
  onboarding: {
    submit: (payload: OnboardingPayload) =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.post<UserProfile>('/api/onboarding', payload);
          return data;
        },
        { ...mockUser, ...payload, id: 'stu-new', onboardingComplete: true },
      ),
    getProfile: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<UserProfile>('/api/onboarding');
          return data;
        },
        mockUser,
      ),
  },

  dashboard: {
    get: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<DashboardData>('/api/dashboard');
          return data;
        },
        mockDashboard,
      ),
    getStatus: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get('/api/status');
          return data;
        },
        mockAIStatus,
      ),
  },

  jobs: {
    getAll: (filters?: Partial<JobFilters>) =>
      withMockFallback(
        async () => {
          const params = new URLSearchParams();
          if (filters?.search) params.append('search', filters.search);
          if (filters?.roles?.length) params.append('roles', filters.roles.join(','));
          if (filters?.companies?.length) params.append('companies', filters.companies.join(','));
          if (filters?.locations?.length) params.append('locations', filters.locations.join(','));
          if (filters?.workModes?.length) params.append('workModes', filters.workModes.join(','));
          if (filters?.employmentTypes?.length) params.append('employmentTypes', filters.employmentTypes.join(','));
          if (filters?.companyTypes?.length) params.append('companyTypes', filters.companyTypes.join(','));
          if (filters?.skills?.length) params.append('skills', filters.skills.join(','));
          
          const { data } = await apiClient.get<JobListing[]>('/api/jobs', { params });
          return data;
        },
        mockJobs,
      ),
  },

  resume: {
    get: async () => {
      try {
        const { data } = await apiClient.get<ResumeAnalysis>('/api/resume');
        return data;
      } catch (err) {
        if (USE_MOCK) return mockResume;
        throw err;
      }
    },
    upload: async (file: File) => {
      const studentId = localStorage.getItem('pc_student_id') || '00000000-0000-0000-0000-000000000000';
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await apiClient.post(`/api/upload-resume/${studentId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
  },

  interview: {
    get: async () => {
      try {
        const { data } = await apiClient.get<InterviewData>('/api/interview');
        return data;
      } catch (err) {
        if (USE_MOCK) return mockInterview;
        throw err;
      }
    },
    chat: async (history: {role: string, content: string}[]) => {
      const studentId = localStorage.getItem('pc_student_id');
      const { data } = await apiClient.post('/api/interview/chat', { 
        student_id: studentId,
        history 
      });
      return data.reply;
    },
  },

  career: {
    get: async () => {
      try {
        const { data } = await apiClient.get<CareerData>('/api/career');
        return data;
      } catch (err) {
        if (USE_MOCK) return mockCareer;
        throw err;
      }
    },
  },

  applications: {
    apply: (jobId: string) =>
      withMockFallback(
        async () => {
          const studentId = localStorage.getItem('pc_student_id');
          if (!studentId) {
            throw new Error('No student profile found');
          }
          const { data } = await apiClient.post(`/api/apply/${studentId}/${jobId}`);
          return data;
        },
        { success: true, jobId, status: 'applied' },
      ),
  },

  tracker: {
    get: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<TrackerData>('/api/tracker');
          return data;
        },
        mockTracker,
      ),
    updateStage: (applicationId: string, stage: string) =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.put(`/api/tracker/${applicationId}`, { stage });
          return data;
        },
        { id: applicationId, stage },
      ),
  },
};

export type ApiClient = typeof api;

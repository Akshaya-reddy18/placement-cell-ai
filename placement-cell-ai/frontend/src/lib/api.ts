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
  return await fetcher();
}

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('pc_token');
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
  (error: AxiosError<{ message?: string }>) => {
    const message = error.response?.data?.message ?? error.message ?? 'Request failed';
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
    getAll: (params?: Record<string, string>) =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<JobListing[]>('/api/jobs', { params });
          return data;
        },
        mockJobs,
      ),
  },

  resume: {
    get: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<ResumeAnalysis>('/api/resume');
          return data;
        },
        mockResume,
      ),
    upload: (file: File) =>
      withMockFallback(
        async () => {
          const studentId = localStorage.getItem('pc_student_id');
          if (!studentId) throw new Error('No student profile found');
          
          const formData = new FormData();
          formData.append('file', file);
          
          const { data } = await apiClient.post(`/api/upload-resume/${studentId}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
          return data;
        },
        { filename: file.name, message: 'Mock upload successful' }
      ),
  },

  interview: {
    get: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<InterviewData>('/api/interview');
          return data;
        },
        mockInterview,
      ),
    chat: (history: {role: string, content: string}[]) =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.post('/api/interview/chat', { history });
          return data.reply;
        },
        "This is a mock response from the AI interviewer. Could you elaborate?"
      )
  },

  career: {
    get: () =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.get<CareerData>('/api/career');
          return data;
        },
        mockCareer,
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
    updateApplication: (id: string, stage: string) =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.put(`/api/tracker/${id}`, { stage });
          return data;
        },
        { success: true, id, stage },
      ),
  },

  applications: {
    updateApplication: (id: string, stage: string) =>
      withMockFallback(
        async () => {
          const { data } = await apiClient.put(`/api/tracker/${id}`, { stage });
          return data;
        },
        { success: true, id, stage },
      ),
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
};

export type ApiClient = typeof api;

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAppStore } from '@/store/useStore';

export function useDashboard() {
  const setDashboard = useAppStore((s) => s.setDashboard);
  const setAIStatus = useAppStore((s) => s.setAIStatus);

  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const [dashboard, status] = await Promise.all([
        api.dashboard.get(),
        api.dashboard.getStatus(),
      ]);
      setDashboard(dashboard);
      setAIStatus(status as Parameters<typeof setAIStatus>[0]);
      return dashboard;
    },
  });
}

export function useJobs() {
  const setJobs = useAppStore((s) => s.setJobs);
  const filters = useAppStore((s) => s.jobFilters);

  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: async () => {
      const jobs = await api.jobs.getAll();
      setJobs(jobs);
      return jobs;
    },
  });
}

export function useResume() {
  const setResume = useAppStore((s) => s.setResume);

  return useQuery({
    queryKey: ['resume'],
    queryFn: async () => {
      const resume = await api.resume.get();
      setResume(resume);
      return resume;
    },
  });
}

export function useInterview() {
  const setInterview = useAppStore((s) => s.setInterview);

  return useQuery({
    queryKey: ['interview'],
    queryFn: async () => {
      const interview = await api.interview.get();
      setInterview(interview);
      return interview;
    },
  });
}

export function useCareer() {
  const setCareer = useAppStore((s) => s.setCareer);

  return useQuery({
    queryKey: ['career'],
    queryFn: async () => {
      const career = await api.career.get();
      setCareer(career);
      return career;
    },
  });
}

export function useTracker() {
  const setTracker = useAppStore((s) => s.setTracker);

  return useQuery({
    queryKey: ['tracker'],
    queryFn: async () => {
      const tracker = await api.tracker.get();
      setTracker(tracker);
      return tracker;
    },
  });
}

export function useOnboardingSubmit() {
  const completeOnboarding = useAppStore((s) => s.completeOnboarding);

  return async (payload: Parameters<typeof api.onboarding.submit>[0]) => {
    const user = await api.onboarding.submit(payload);
    completeOnboarding(user);
    localStorage.setItem('pc_student_id', user.id);
    return user;
  };
}

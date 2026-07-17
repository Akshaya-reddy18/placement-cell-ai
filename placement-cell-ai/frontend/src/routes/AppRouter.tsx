import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute, PublicOnlyRoute } from '@/components/layout/ProtectedRoute';
import CareerPage from '@/pages/Career';
import DashboardPage from '@/pages/Dashboard';
import InterviewPage from '@/pages/Interview';
import JobsPage from '@/pages/Jobs';
import OnboardingPage from '@/pages/Onboarding';
import ResumePage from '@/pages/Resume';
import SettingsPage from '@/pages/Settings';
import TrackerPage from '@/pages/Tracker';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route index element={<OnboardingPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route path="resume" element={<ResumePage />} />
            <Route path="interview" element={<InterviewPage />} />
            <Route path="career" element={<CareerPage />} />
            <Route path="tracker" element={<TrackerPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

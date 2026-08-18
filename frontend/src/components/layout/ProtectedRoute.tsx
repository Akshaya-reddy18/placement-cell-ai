import { Navigate, Outlet } from 'react-router-dom';
import { useIsOnboarded } from '@/store/useStore';

export function ProtectedRoute() {
  const isOnboarded = useIsOnboarded();
  const token = localStorage.getItem('pc_token');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!isOnboarded) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const isOnboarded = useIsOnboarded();
  const token = localStorage.getItem('pc_token');

  if (token && isOnboarded) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

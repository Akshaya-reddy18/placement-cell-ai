import { Navigate, Outlet } from 'react-router-dom';
import { useIsOnboarded } from '@/store/useStore';

export function ProtectedRoute() {
  const isOnboarded = useIsOnboarded();

  if (!isOnboarded) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const isOnboarded = useIsOnboarded();

  if (isOnboarded) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

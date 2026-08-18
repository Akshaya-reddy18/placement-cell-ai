import { NavLink } from 'react-router-dom';
import {
  Briefcase,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Target,
  Kanban,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/resume', label: 'Resume Optimizer', icon: FileText },
  { to: '/interview', label: 'Interview Prep', icon: MessageSquare },
  { to: '/career', label: 'Career Strategy', icon: Target },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-slate-800 bg-slate-950">
      <div className="flex h-14 items-center gap-2 border-b border-slate-800 px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-100 text-xs font-bold text-slate-950">
          PC
        </div>
        <div>
          <p className="text-sm font-medium text-slate-100">Placement Cell</p>
          <p className="text-[10px] text-slate-500">AI Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-slate-800 text-slate-100'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200',
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800 p-4">
        <button
          onClick={async () => {
            await import('@/lib/supabase').then(m => m.supabase.auth.signOut());
            localStorage.removeItem('pc_token');
            const { useAppStore } = await import('@/store/useStore');
            useAppStore.getState().setUser(null);
            window.location.href = '/login';
          }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 transition-colors hover:bg-slate-900 hover:text-red-400"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="shrink-0"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          Log out
        </button>
        <p className="mt-4 text-xs text-slate-500">Powered by Gemini AI</p>
      </div>
    </aside>
  );
}

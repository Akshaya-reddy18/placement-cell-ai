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
        <p className="text-xs text-slate-500">Powered by Gemini AI</p>
      </div>
    </aside>
  );
}

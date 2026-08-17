import { Bell, Loader2, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useAppStore } from '@/store/useStore';

export function Header() {
  const user = useAppStore((s) => s.user);
  const aiStatus = useAppStore((s) => s.aiStatus);
  const useMockData = import.meta.env.VITE_USE_MOCK !== 'false';
  const isAnalyzing = !useMockData && aiStatus.status === 'running';
  const statusLabel = useMockData ? 'Demo data' : `AI ${aiStatus.percentage}%`;
  const statusBadge = useMockData ? 'idle' : aiStatus.status;

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-slate-800 bg-slate-950 px-4 sm:px-6">
      <div className="relative hidden max-w-md flex-1 sm:block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <Input placeholder="Search jobs, companies, skills..." className="pl-9" />
      </div>

      <div className="flex flex-1 items-center justify-end gap-3 sm:flex-none">
        <div className="hidden items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-1.5 sm:flex">
          {isAnalyzing ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400" />
          ) : (
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
          )}
          <span className="text-xs text-slate-400">{statusLabel}</span>
          <StatusBadge status={statusBadge} />
        </div>

        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 text-slate-400 transition-colors hover:border-slate-700 hover:text-slate-200"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2 rounded-lg border border-slate-800 px-2 py-1">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-800 text-xs font-medium text-slate-300">
            {user?.name?.charAt(0) ?? 'U'}
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-slate-200">{user?.name ?? 'Student'}</p>
            <p className="text-[10px] text-slate-500">{user?.email ?? ''}</p>
          </div>
        </div>
      </div>
    </header>
  );
}

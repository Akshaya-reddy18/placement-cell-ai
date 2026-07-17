import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 px-6 py-16 text-center',
        className,
      )}
    >
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-slate-800 bg-slate-900">
        <Icon className="h-5 w-5 text-slate-500" />
      </div>
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-slate-500">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

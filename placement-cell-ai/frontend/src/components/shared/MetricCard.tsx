import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
  className?: string;
}

export function MetricCard({ label, value, change, trend = 'neutral', icon: Icon, className }: MetricCardProps) {
  const trendColor =
    trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-slate-500';

  return (
    <div
      className={cn(
        'rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition-colors hover:border-slate-700',
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-3">
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-2xl font-semibold tracking-tight text-slate-100">{value}</p>
          {change && <p className={cn('text-xs', trendColor)}>{change}</p>}
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-800/50">
          <Icon className="h-4 w-4 text-slate-400" />
        </div>
      </div>
    </div>
  );
}

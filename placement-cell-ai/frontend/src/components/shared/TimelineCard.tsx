import { CheckCircle2, Circle } from 'lucide-react';
import type { CareerMilestone } from '@/types';
import { cn } from '@/lib/utils';

interface TimelineCardProps {
  milestones: CareerMilestone[];
  className?: string;
}

const statusIcon = {
  completed: CheckCircle2,
  in_progress: Circle,
  upcoming: Circle,
};

const statusColor = {
  completed: 'text-emerald-400 border-emerald-500/30',
  in_progress: 'text-slate-300 border-slate-600',
  upcoming: 'text-slate-600 border-slate-800',
};

export function TimelineCard({ milestones, className }: TimelineCardProps) {
  return (
    <div className={cn('space-y-0', className)}>
      {milestones.map((milestone, index) => {
        const Icon = statusIcon[milestone.status];
        const isLast = index === milestones.length - 1;

        return (
          <div key={milestone.id} className="relative flex gap-4 pb-8">
            {!isLast && (
              <div className="absolute left-[15px] top-8 h-[calc(100%-16px)] w-px bg-slate-800" />
            )}
            <div
              className={cn(
                'relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-slate-900',
                statusColor[milestone.status],
              )}
            >
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1 pt-0.5">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-medium text-slate-100">{milestone.title}</h4>
                <span className="text-xs text-slate-500">{milestone.quarter}</span>
              </div>
              <p className="mt-1 text-sm text-slate-400">{milestone.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

import { Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface AIInsightCardProps {
  title: string;
  description: string;
  type?: 'tip' | 'warning' | 'success' | 'action';
  className?: string;
}

const typeBadge = {
  tip: { label: 'Insight', variant: 'default' as const },
  warning: { label: 'Attention', variant: 'warning' as const },
  success: { label: 'Strength', variant: 'success' as const },
  action: { label: 'Action', variant: 'default' as const },
};

export function AIInsightCard({ title, description, type = 'tip', className }: AIInsightCardProps) {
  const badge = typeBadge[type];

  return (
    <div
      className={cn(
        'rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition-colors hover:border-slate-700',
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-800 bg-slate-800/50">
          <Sparkles className="h-4 w-4 text-slate-400" />
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-medium text-slate-100">{title}</h4>
            <Badge variant={badge.variant}>{badge.label}</Badge>
          </div>
          <p className="text-sm leading-relaxed text-slate-400">{description}</p>
        </div>
      </div>
    </div>
  );
}

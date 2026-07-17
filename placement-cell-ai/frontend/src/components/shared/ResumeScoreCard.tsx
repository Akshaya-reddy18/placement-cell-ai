import { ProgressRing } from '@/components/shared/ProgressRing';
import { cn } from '@/lib/utils';

interface ScoreItem {
  label: string;
  value: number;
}

interface ResumeScoreCardProps {
  overall: number;
  scores: ScoreItem[];
  className?: string;
}

export function ResumeScoreCard({ overall, scores, className }: ResumeScoreCardProps) {
  return (
    <div className={cn('rounded-xl border border-slate-800 bg-slate-900/40 p-5', className)}>
      <div className="flex items-center gap-6">
        <ProgressRing value={overall} size={96} label="Overall" />
        <div className="grid flex-1 gap-3 sm:grid-cols-2">
          {scores.map((score) => (
            <div key={score.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">{score.label}</span>
                <span className="font-medium text-slate-200">{score.value}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-slate-400 transition-all"
                  style={{ width: `${score.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

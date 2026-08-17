import { Badge } from '@/components/ui/badge';
import type { InterviewQuestion } from '@/types';
import { cn } from '@/lib/utils';

interface InterviewCardProps {
  question: InterviewQuestion;
  className?: string;
}

const difficultyVariant = {
  easy: 'success' as const,
  medium: 'warning' as const,
  hard: 'danger' as const,
};

export function InterviewCard({ question, className }: InterviewCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition-colors hover:border-slate-700',
        className,
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        <Badge variant="outline">{question.type.replace('_', ' ')}</Badge>
        <Badge variant={difficultyVariant[question.difficulty]}>{question.difficulty}</Badge>
        <span className="text-xs text-slate-500">{question.topic}</span>
      </div>
      <p className="text-sm leading-relaxed text-slate-200">{question.question}</p>
    </div>
  );
}

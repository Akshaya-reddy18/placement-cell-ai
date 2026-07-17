import { Building2, MapPin } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/StatusBadge';
import type { JobListing } from '@/types';
import { cn } from '@/lib/utils';

interface JobCardProps {
  job: JobListing;
  compact?: boolean;
  onViewDetails?: () => void;
  onApply?: () => void;
  className?: string;
}

export function JobCard({ job, compact = false, onViewDetails, onApply, className }: JobCardProps) {
  return (
    <article
      className={cn(
        'rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition-colors hover:border-slate-700',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-3">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-800/50">
              <Building2 className="h-4 w-4 text-slate-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-100">{job.title}</h3>
              <p className="text-xs text-slate-500">{job.company}</p>
            </div>
          </div>

          {!compact && (
            <p className="line-clamp-2 text-sm text-slate-400">{job.description}</p>
          )}

          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {job.location}
            </span>
            {job.salary && <span>{job.salary}</span>}
            <span>{job.postedAt}</span>
          </div>

          {!compact && (
            <div className="flex flex-wrap gap-1.5">
              {job.requirements.slice(0, 4).map((skill) => (
                <Badge key={skill} variant="outline">{skill}</Badge>
              ))}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          <div className="text-right">
            <p className="text-lg font-semibold text-slate-100">{job.matchPercentage}%</p>
            <p className="text-xs text-slate-500">match</p>
          </div>
          <StatusBadge status={job.priority} />
        </div>
      </div>

      {(onViewDetails || onApply) && (
        <div className="mt-4 border-t border-slate-800 pt-4">
          <div className="grid gap-2 sm:grid-cols-2">
            {onViewDetails && (
              <Button variant="outline" size="sm" className="w-full" onClick={onViewDetails}>
                View details
              </Button>
            )}
            {onApply && (
              <Button size="sm" className="w-full" onClick={onApply}>
                Apply
              </Button>
            )}
          </div>
        </div>
      )}
    </article>
  );
}

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SectionCardProps {
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
  headerAction?: ReactNode;
}

export function SectionCard({ title, description, children, className, headerAction }: SectionCardProps) {
  return (
    <section className={cn('rounded-xl border border-slate-800 bg-slate-900/40', className)}>
      {(title || headerAction) && (
        <div className="flex items-start justify-between border-b border-slate-800 px-5 py-4">
          <div>
            {title && <h2 className="text-sm font-medium text-slate-100">{title}</h2>}
            {description && <p className="mt-1 text-xs text-slate-500">{description}</p>}
          </div>
          {headerAction}
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

import { useMemo } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import { useDraggable, useDroppable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { useState } from 'react';
import { GripVertical, Kanban } from 'lucide-react';
import { AnalyticsChart } from '@/components/shared/AnalyticsChart';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingState } from '@/components/shared/LoadingState';
import { PageHeader } from '@/components/shared/PageHeader';
import { SectionCard } from '@/components/shared/SectionCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useTracker } from '@/hooks/useQueries';
import { useAppStore } from '@/store/useStore';
import type { ApplicationCard, ApplicationStage } from '@/types';
import { cn } from '@/lib/utils';

const COLUMNS: { id: ApplicationStage; label: string }[] = [
  { id: 'wishlist', label: 'Wishlist' },
  { id: 'applied', label: 'Applied' },
  { id: 'oa', label: 'OA' },
  { id: 'interview', label: 'Interview' },
  { id: 'offer', label: 'Offer' },
  { id: 'rejected', label: 'Rejected' },
];

export default function TrackerPage() {
  const { data, isLoading, isError } = useTracker();
  const moveApplication = useAppStore((s) => s.moveApplication);
  const tracker = useAppStore((s) => s.tracker) ?? data;
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const applications = tracker?.applications ?? [];

  const grouped = useMemo(() => {
    const map: Record<ApplicationStage, ApplicationCard[]> = {
      wishlist: [],
      applied: [],
      oa: [],
      interview: [],
      offer: [],
      rejected: [],
    };
    applications.forEach((app) => map[app.stage].push(app));
    return map;
  }, [applications]);

  const activeCard = applications.find((a) => a.id === activeId);

  const handleDragStart = (event: DragStartEvent) => setActiveId(String(event.active.id));
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (over && active.id !== over.id) {
      moveApplication(String(active.id), over.id as ApplicationStage);
    }
  };

  if (isLoading) return <LoadingState />;
  if (isError || !tracker) {
    return (
      <EmptyState
        icon={Kanban}
        title="Tracker unavailable"
        description="Start applying to jobs to track your placement pipeline."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Tracker"
        description="Track every application from wishlist to offer."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Apply → OA" value={`${tracker.analytics.conversionRates.applyToOa}%`} />
        <StatCard label="OA → Interview" value={`${tracker.analytics.conversionRates.oaToInterview}%`} />
        <StatCard label="Interview → Offer" value={`${tracker.analytics.conversionRates.interviewToOffer}%`} />
      </div>

      <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <KanbanColumn key={col.id} id={col.id} label={col.label} count={grouped[col.id].length}>
              {grouped[col.id].map((app) => (
                <DraggableCard key={app.id} app={app} />
              ))}
            </KanbanColumn>
          ))}
        </div>
        <DragOverlay>
          {activeCard ? <ApplicationCardUI app={activeCard} isDragging /> : null}
        </DragOverlay>
      </DndContext>

      <SectionCard title="Applications by stage">
        <AnalyticsChart
          data={tracker.analytics.byStage.map((s) => ({ name: s.stage, count: s.count }))}
          dataKeys={['count']}
          type="bar"
          height={220}
        />
      </SectionCard>
    </div>
  );
}

function KanbanColumn({
  id,
  label,
  count,
  children,
}: {
  id: ApplicationStage;
  label: string;
  count: number;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex w-64 shrink-0 flex-col rounded-xl border bg-slate-900/30',
        isOver ? 'border-slate-600' : 'border-slate-800',
      )}
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <span className="text-sm font-medium text-slate-200">{label}</span>
        <Badge variant="outline">{count}</Badge>
      </div>
      <div className="flex flex-1 flex-col gap-2 p-3 min-h-[320px]">{children}</div>
    </div>
  );
}

function DraggableCard({ app }: { app: ApplicationCard }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: app.id });

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  return (
    <div ref={setNodeRef} style={style} className={cn(isDragging && 'opacity-40')}>
      <ApplicationCardUI app={app} dragHandleProps={{ ...attributes, ...listeners }} />
    </div>
  );
}

function ApplicationCardUI({
  app,
  dragHandleProps,
  isDragging,
}: {
  app: ApplicationCard;
  dragHandleProps?: Record<string, unknown>;
  isDragging?: boolean;
}) {
  return (
    <div
      className={cn(
        'rounded-lg border border-slate-800 bg-slate-900/60 p-3',
        isDragging && 'shadow-lg ring-1 ring-slate-700',
      )}
    >
      <div className="mb-2 flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-100">{app.company}</p>
          <p className="text-xs text-slate-500">{app.role}</p>
        </div>
        <button type="button" className="cursor-grab text-slate-600 hover:text-slate-400" {...dragHandleProps}>
          <GripVertical className="h-4 w-4" />
        </button>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-slate-500">{app.date}</span>
        <StatusBadge status={app.priority} />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-5 py-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-100">{value}</p>
    </div>
  );
}

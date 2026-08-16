import {
  Briefcase,
  Calendar,
  FileText,
  Target,
  TrendingUp,
} from 'lucide-react';
import { AIInsightCard } from '@/components/shared/AIInsightCard';
import { AnalyticsChart } from '@/components/shared/AnalyticsChart';
import { EmptyState } from '@/components/shared/EmptyState';
import { JobCard } from '@/components/shared/JobCard';
import { LoadingState } from '@/components/shared/LoadingState';
import { MetricCard } from '@/components/shared/MetricCard';
import { PageHeader } from '@/components/shared/PageHeader';
import { ProgressRing } from '@/components/shared/ProgressRing';
import { SectionCard } from '@/components/shared/SectionCard';
import { useAppStore } from '@/store/useStore';
import { useDashboard } from '@/hooks/useQueries';
import { Bot, AlertTriangle } from 'lucide-react';

export default function DashboardPage() {
  const { data, isLoading, isError } = useDashboard();
  const aiStatus = useAppStore((s) => s.aiStatus);

  if (isLoading) return <LoadingState />;

  if (aiStatus.status === 'pending' || aiStatus.status === 'running') {
    return (
      <EmptyState
        icon={Bot}
        title="AI Analysis in Progress"
        description={`Your personalized dashboard is being generated. Current step: ${aiStatus.currentAgent} (${aiStatus.percentage}%)`}
      />
    );
  }

  if (aiStatus.status === 'failed') {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Analysis Failed"
        description={`There was an error generating your dashboard: ${aiStatus.errorMessage || 'Unknown error'}`}
      />
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        icon={TrendingUp}
        title="Unable to load dashboard"
        description="Something went wrong fetching your placement data."
      />
    );
  }

  const { metrics, insights, deadlines, recommendedJobs, chartData, readinessBreakdown } = data;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Your placement command center — track progress, insights, and next actions."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Applications" value={metrics.applications} change="+3 this month" trend="up" icon={Briefcase} />
        <MetricCard label="Resume Score" value={`${metrics.resumeScore}%`} change="+6 pts" trend="up" icon={FileText} />
        <MetricCard label="Interview Readiness" value={`${metrics.interviewReadiness}%`} change="Needs practice" trend="neutral" icon={Target} />
        <MetricCard label="Placement Probability" value={`${metrics.placementProbability}%`} change="On track" trend="up" icon={TrendingUp} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <SectionCard title="Application activity" className="lg:col-span-2">
          <AnalyticsChart data={chartData} type="bar" />
        </SectionCard>

        <SectionCard title="Placement readiness">
          <div className="flex flex-col items-center gap-6 py-2">
            <ProgressRing value={metrics.placementReadiness} size={120} label="Overall" />
            <div className="w-full space-y-3">
              {readinessBreakdown.map((item) => (
                <div key={item.name} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">{item.name}</span>
                    <span className="text-slate-200">{item.value}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-800">
                    <div className="h-full rounded-full bg-slate-400" style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Recent AI insights">
          <div className="space-y-3">
            {insights.map((insight) => (
              <AIInsightCard
                key={insight.id}
                title={insight.title}
                description={insight.description}
                type={insight.type}
              />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Upcoming deadlines">
          <div className="space-y-3">
            {deadlines.map((deadline) => (
              <div
                key={deadline.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-slate-500" />
                  <div>
                    <p className="text-sm text-slate-200">{deadline.title}</p>
                    <p className="text-xs text-slate-500">{deadline.company}</p>
                  </div>
                </div>
                <span className="text-xs text-slate-400">{deadline.dueDate}</span>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Recommended jobs">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {recommendedJobs.map((job) => (
            <JobCard key={job.id} job={job} compact />
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

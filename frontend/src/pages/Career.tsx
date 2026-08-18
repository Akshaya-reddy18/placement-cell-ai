import { Target, TrendingUp } from 'lucide-react';
import { AnalyticsChart } from '@/components/shared/AnalyticsChart';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingState } from '@/components/shared/LoadingState';
import { MetricCard } from '@/components/shared/MetricCard';
import { PageHeader } from '@/components/shared/PageHeader';
import { SectionCard } from '@/components/shared/SectionCard';
import { TimelineCard } from '@/components/shared/TimelineCard';
import { useCareer } from '@/hooks/useQueries';

export default function CareerPage() {
  const { data, isLoading, isError } = useCareer();

  if (isLoading) return <LoadingState />;
  if (isError || !data) {
    return (
      <EmptyState
        icon={Target}
        title="Career strategy unavailable"
        description="Complete your profile analysis to generate a personalized career roadmap."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.targetRole ? `Career Strategy · ${data.targetRole}` : "Career Strategy"}
        description={
          data.targetRole
            ? `Personalized placement roadmap, skill gaps, and learning track tailored for ${data.targetRole} roles at ${data.targetCompanies?.slice(0, 3).join(', ') || 'top companies'}.`
            : "Executive-style placement planning — roadmap, skill gaps, and market insights."
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          label={`Focus Strategy · ${data.targetRole || 'Target Role'}`}
          value={data.focusRecommendation}
          icon={Target}
        />
        <MetricCard
          label="Placement Probability"
          value={`${data.placementProbability}%`}
          change={`Calibrated for ${data.targetRole || 'Target Role'}`}
          trend="up"
          icon={TrendingUp}
        />
        <MetricCard
          label="Package Projection"
          value={`₹${data.packageProjection.min}-${data.packageProjection.max} LPA`}
          change="Target Company Tier"
          icon={TrendingUp}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title={`Career Roadmap · ${data.targetRole || 'Milestones'}`}>
          <TimelineCard milestones={data.milestones} />
        </SectionCard>

        <SectionCard title={`Skill Gap Analysis · ${data.targetRole || 'Target Role'}`}>
          <div className="space-y-3">
            {data.skillGaps.map((gap) => (
              <div
                key={gap.skill}
                className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm text-slate-200">{gap.skill}</span>
                  <Badge variant={gap.priority === 'critical' ? 'danger' : 'outline'}>
                    {gap.priority.replace('_', ' ')}
                  </Badge>
                </div>
                <span className="text-xs text-slate-500">{gap.marketDemand}% demand</span>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title={`Learning Recommendations · ${data.targetRole || 'Target Role'}`}>
          <ul className="space-y-3">
            {data.learningRecommendations.map((rec, i) => (
              <li key={i} className="flex gap-3 text-sm text-slate-300">
                <span className="text-slate-500 font-semibold">{i + 1}.</span>
                {rec}
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Market Demand Insights">
          <AnalyticsChart
            data={data.marketInsights.map((m) => ({ name: m.skill, demand: m.demand, growth: m.growth }))}
            dataKeys={['demand']}
            type="bar"
            height={240}
          />
        </SectionCard>
      </div>

      <SectionCard title={`Target Company Roadmap · ${data.targetRole || 'Target Role'}`}>
        <p className="text-xs text-slate-400 mb-3">
          Tailored company pathway and hiring loops for your selected target companies:
        </p>
        <div className="flex flex-wrap gap-2">
          {data.targetCompanies.map((company) => (
            <Badge key={company} variant="default" className="text-sm py-1 px-3">
              {company}
            </Badge>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

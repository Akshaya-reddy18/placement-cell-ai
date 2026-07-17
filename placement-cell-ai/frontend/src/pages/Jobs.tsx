import { useMemo } from 'react';
import { Briefcase, Sparkles } from 'lucide-react';
import { AIInsightCard } from '@/components/shared/AIInsightCard';
import { EmptyState } from '@/components/shared/EmptyState';
import { JobCard } from '@/components/shared/JobCard';
import { LoadingState } from '@/components/shared/LoadingState';
import { PageHeader } from '@/components/shared/PageHeader';
import { SearchBar } from '@/components/shared/SearchBar';
import { SectionCard } from '@/components/shared/SectionCard';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useJobs } from '@/hooks/useQueries';
import { useAppStore } from '@/store/useStore';

const FILTER_OPTIONS = {
  companies: ['Razorpay', 'Postman', 'Freshworks', 'Swiggy', 'Atlassian', 'Amazon'],
  locations: ['Bangalore', 'Chennai', 'Hyderabad', 'Remote — India'],
  skills: ['Python', 'React', 'TypeScript', 'FastAPI', 'Docker', 'PostgreSQL'],
};

export default function JobsPage() {
  const { data: jobs = [], isLoading, isError } = useJobs();
  const filters = useAppStore((s) => s.jobFilters);
  const setJobFilters = useAppStore((s) => s.setJobFilters);

  const openJobDetails = (job: (typeof jobs)[number]) => {
    const destination =
      job.url ||
      `https://www.google.com/search?q=${encodeURIComponent(`${job.company} ${job.title} careers`)}`;
    window.open(destination, '_blank', 'noopener,noreferrer');
  };

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const searchMatch =
        !filters.search ||
        job.title.toLowerCase().includes(filters.search.toLowerCase()) ||
        job.company.toLowerCase().includes(filters.search.toLowerCase());
      const companyMatch =
        filters.companies.length === 0 || filters.companies.includes(job.company);
      const locationMatch =
        filters.locations.length === 0 || filters.locations.includes(job.location);
      const skillMatch =
        filters.skills.length === 0 ||
        filters.skills.some((s) => job.requirements.includes(s));
      return searchMatch && companyMatch && locationMatch && skillMatch;
    });
  }, [jobs, filters]);

  const toggleFilter = (key: 'companies' | 'locations' | 'skills', value: string) => {
    const current = filters[key];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    setJobFilters({ [key]: next });
  };

  if (isLoading) return <LoadingState />;
  if (isError) {
    return (
      <EmptyState
        icon={Briefcase}
        title="No jobs available"
        description="We couldn't load job listings. Try again later."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        description="Discover roles matched to your skills and career goals."
      />

      <div className="grid gap-6 lg:grid-cols-[240px_1fr_280px]">
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <SectionCard title="Filters">
            <div className="space-y-5">
              <FilterGroup
                title="Company"
                options={FILTER_OPTIONS.companies}
                selected={filters.companies}
                onToggle={(v) => toggleFilter('companies', v)}
              />
              <FilterGroup
                title="Location"
                options={FILTER_OPTIONS.locations}
                selected={filters.locations}
                onToggle={(v) => toggleFilter('locations', v)}
              />
              <FilterGroup
                title="Skills"
                options={FILTER_OPTIONS.skills}
                selected={filters.skills}
                onToggle={(v) => toggleFilter('skills', v)}
              />
            </div>
          </SectionCard>
        </aside>

        <div className="space-y-4">
          <SearchBar
            value={filters.search}
            onChange={(search) => setJobFilters({ search })}
            placeholder="Search roles or companies..."
          />
          <p className="text-xs text-slate-500">{filteredJobs.length} roles found</p>
          <div className="space-y-3">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onViewDetails={() => openJobDetails(job)}
                onApply={async () => {
                  try {
                    await api.applications.apply(job.id);
                  } finally {
                    openJobDetails(job);
                  }
                }}
              />
            ))}
          </div>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <SectionCard title="AI recommendations">
            <div className="space-y-3">
              <AIInsightCard
                title="Top match: Razorpay"
                description="91% match — your Python and FastAPI skills align perfectly with their backend intern role."
                type="success"
              />
              <AIInsightCard
                title="Skill gap alert"
                description="Add Docker to unlock 3 additional high-match platform engineering roles."
                type="action"
              />
              <div className="rounded-lg border border-slate-800 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-slate-400" />
                  <span className="text-xs font-medium text-slate-300">Apply priority</span>
                </div>
                <ol className="space-y-2 text-xs text-slate-400">
                  <li>1. Razorpay — Backend Engineer Intern</li>
                  <li>2. Postman — Software Engineer</li>
                  <li>3. Freshworks — Full Stack Developer</li>
                </ol>
              </div>
            </div>
          </SectionCard>
        </aside>
      </div>
    </div>
  );
}

function FilterGroup({
  title,
  options,
  selected,
  onToggle,
}: {
  title: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-slate-400">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => onToggle(option)}
            className="cursor-pointer"
          >
            <Badge variant={selected.includes(option) ? 'default' : 'outline'}>{option}</Badge>
          </button>
        ))}
      </div>
    </div>
  );
}

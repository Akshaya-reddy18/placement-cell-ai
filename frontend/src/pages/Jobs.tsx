import { useMemo } from 'react';
import { Briefcase, Sparkles, Building, Star, Compass } from 'lucide-react';
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
import type { JobListing } from '@/types';

const FILTER_OPTIONS = {
  roles: ['Software Engineer', 'Frontend Developer', 'Backend Engineer', 'Data Scientist', 'Product Manager', 'AI Engineer', 'ML Engineer'],
  companies: ['Google', 'Microsoft', 'Amazon', 'Stripe', 'Atlassian', 'Razorpay', 'Swiggy', 'Deloitte'],
  locations: ['Bangalore', 'Chennai', 'Hyderabad', 'Remote', 'Pune'],
  workModes: ['Remote', 'Hybrid', 'On-site'],
  employmentTypes: ['Full-time', 'Internship', 'Contract'],
  companyTypes: ['MNC', 'Startup', 'Product-based', 'Service-based'],
  skills: ['Python', 'React', 'TypeScript', 'FastAPI', 'Docker', 'PostgreSQL', 'Machine Learning'],
};

export default function JobsPage() {
  const { data: jobs = [], isLoading, isError } = useJobs();
  const filters = useAppStore((s) => s.jobFilters);
  const setJobFilters = useAppStore((s) => s.setJobFilters);

  const openJobDetails = (job: JobListing) => {
    const destination = job.apply_url || job.job_url || job.url;
    if (destination && !destination.includes('google.com/search')) {
      window.open(destination, '_blank', 'noopener,noreferrer');
    }
  };

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      // Must have a valid URL
      const hasValidUrl = job.apply_url || job.job_url || job.url;
      if (!hasValidUrl || hasValidUrl.includes('google.com/search')) return false;

      const searchLower = filters.search.toLowerCase();
      const searchMatch =
        !filters.search ||
        job.title.toLowerCase().includes(searchLower) ||
        job.company.toLowerCase().includes(searchLower) ||
        (job.description && job.description.toLowerCase().includes(searchLower));
      
      const roleMatch = filters.roles.length === 0 || filters.roles.some((r) => job.title.toLowerCase().includes(r.toLowerCase()));
      const companyMatch = filters.companies.length === 0 || filters.companies.includes(job.company);
      const locationMatch = filters.locations.length === 0 || filters.locations.includes(job.location);
      const workModeMatch = filters.workModes.length === 0 || (job.work_mode && filters.workModes.includes(job.work_mode));
      const empTypeMatch = filters.employmentTypes.length === 0 || (job.employment_type && filters.employmentTypes.includes(job.employment_type));
      const companyTypeMatch = filters.companyTypes.length === 0 || (job.company_type && filters.companyTypes.includes(job.company_type));
      
      const skillMatch =
        filters.skills.length === 0 ||
        filters.skills.some((s) => job.requirements && job.requirements.includes(s));
        
      return searchMatch && roleMatch && companyMatch && locationMatch && workModeMatch && empTypeMatch && companyTypeMatch && skillMatch;
    });
  }, [jobs, filters]);

  const { recommended, preferred, related } = useMemo(() => {
    const sorted = [...filteredJobs].sort((a, b) => b.matchPercentage - a.matchPercentage);
    
    // Top 5 highest matching
    const topRecommended = sorted.slice(0, 5);
    const recommendedIds = new Set(topRecommended.map(j => j.id));
    
    // Preferred companies
    const preferredCompanyJobs = sorted.filter(j => 
      filters.companies.length > 0 && filters.companies.includes(j.company) && !recommendedIds.has(j.id)
    );
    const preferredIds = new Set(preferredCompanyJobs.map(j => j.id));
    
    // Everything else
    const relatedJobs = sorted.filter(j => !recommendedIds.has(j.id) && !preferredIds.has(j.id));
    
    return {
      recommended: topRecommended,
      preferred: preferredCompanyJobs,
      related: relatedJobs
    };
  }, [filteredJobs, filters.companies]);

  const toggleFilter = (key: keyof typeof FILTER_OPTIONS, value: string) => {
    const current = filters[key] as string[];
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
        title="Unable to load jobs"
        description="We encountered an error connecting to job providers. Please try again."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        description="Discover real, open roles matched to your skills and preferences."
      />

      <div className="grid gap-6 lg:grid-cols-[240px_1fr_280px]">
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <SectionCard title="Preferences (Multi-select)">
            <div className="space-y-5">
              <FilterGroup
                title="Companies"
                options={FILTER_OPTIONS.companies}
                selected={filters.companies}
                onToggle={(v) => toggleFilter('companies', v)}
              />
              <FilterGroup
                title="Roles"
                options={FILTER_OPTIONS.roles}
                selected={filters.roles}
                onToggle={(v) => toggleFilter('roles', v)}
              />
              <FilterGroup
                title="Locations"
                options={FILTER_OPTIONS.locations}
                selected={filters.locations}
                onToggle={(v) => toggleFilter('locations', v)}
              />
              <FilterGroup
                title="Work Mode"
                options={FILTER_OPTIONS.workModes}
                selected={filters.workModes}
                onToggle={(v) => toggleFilter('workModes', v)}
              />
              <FilterGroup
                title="Employment Type"
                options={FILTER_OPTIONS.employmentTypes}
                selected={filters.employmentTypes}
                onToggle={(v) => toggleFilter('employmentTypes', v)}
              />
              <FilterGroup
                title="Company Type"
                options={FILTER_OPTIONS.companyTypes}
                selected={filters.companyTypes}
                onToggle={(v) => toggleFilter('companyTypes', v)}
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

        <div className="space-y-8">
          <div>
            <SearchBar
              value={filters.search}
              onChange={(search) => setJobFilters({ search })}
              placeholder="Search roles or companies..."
            />
            <p className="mt-2 text-xs text-slate-500">{filteredJobs.length} roles found</p>
          </div>

          {filteredJobs.length === 0 ? (
            <EmptyState
              icon={Compass}
              title="No matching jobs found"
              description="Try expanding your location, role, work-mode or company preferences."
            />
          ) : (
            <>
              {recommended.length > 0 && (
                <section className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <Star className="h-5 w-5 text-yellow-500" />
                    <h2 className="text-lg font-semibold text-slate-100">Recommended For You</h2>
                  </div>
                  <div className="space-y-3">
                    {recommended.map(job => (
                      <JobCard key={job.id} job={job} onApply={() => openJobDetails(job)} />
                    ))}
                  </div>
                </section>
              )}

              {preferred.length > 0 && (
                <section className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <Building className="h-5 w-5 text-blue-400" />
                    <h2 className="text-lg font-semibold text-slate-100">Preferred Companies</h2>
                  </div>
                  <div className="space-y-3">
                    {preferred.map(job => (
                      <JobCard key={job.id} job={job} onApply={() => openJobDetails(job)} />
                    ))}
                  </div>
                </section>
              )}

              {related.length > 0 && (
                <section className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <Compass className="h-5 w-5 text-emerald-400" />
                    <h2 className="text-lg font-semibold text-slate-100">Related Opportunities</h2>
                  </div>
                  <div className="space-y-3">
                    {related.map(job => (
                      <JobCard key={job.id} job={job} onApply={() => openJobDetails(job)} />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <SectionCard title="AI recommendations">
            <div className="space-y-3">
              {jobs.length > 0 ? (
                <>
                  <AIInsightCard
                    title={`Top match: ${jobs[0].company}`}
                    description={`${jobs[0].matchPercentage}% match — this role aligns well with your profile.`}
                    type="success"
                  />
                  <AIInsightCard
                    title="Action needed"
                    description="Tailor your resume for the top matches to increase your chances."
                    type="action"
                  />
                  <div className="rounded-lg border border-slate-800 p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-slate-400" />
                      <span className="text-xs font-medium text-slate-300">Apply priority</span>
                    </div>
                    <ol className="space-y-2 text-xs text-slate-400">
                      {recommended.slice(0, 3).map((job, idx) => (
                        <li key={job.id}>{idx + 1}. {job.company} — {job.title}</li>
                      ))}
                    </ol>
                  </div>
                </>
              ) : (
                <div className="text-sm text-slate-500 text-center py-4">
                  No recommendations available yet.
                </div>
              )}
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


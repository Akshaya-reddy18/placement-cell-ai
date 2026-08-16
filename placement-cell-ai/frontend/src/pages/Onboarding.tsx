import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ProgressRing } from '@/components/shared/ProgressRing';
import { useOnboardingSubmit } from '@/hooks/useQueries';
import type { CareerGoals, OnboardingPayload } from '@/types';
import { cn } from '@/lib/utils';

const STEPS = ['Profile', 'Skills', 'Companies', 'Resume', 'Goals'];

const defaultGoals: CareerGoals = {
  preferredRoles: [],
  targetCompanies: [],
  workPreference: 'hybrid',
  locations: ['Bangalore'],
  workModes: ['Hybrid', 'Remote'],
  employmentTypes: ['Full-time'],
  companyTypes: ['MNC', 'Startup'],
  requiredConstraints: [],
  salaryExpectation: '12-18 LPA',
};

export default function OnboardingPage() {
  const navigate = useNavigate();
  const submitOnboarding = useOnboardingSubmit();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [skillInput, setSkillInput] = useState('');
  const [companyInput, setCompanyInput] = useState('');

  const [form, setForm] = useState<OnboardingPayload>({
    name: '',
    email: '',
    college: '',
    branch: 'Computer Science',
    graduationYear: 2026,
    skills: [],
    targetCompanies: [],
    careerGoals: defaultGoals,
  });

  const update = (patch: Partial<OnboardingPayload>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const addSkill = () => {
    if (skillInput.trim() && !form.skills.includes(skillInput.trim())) {
      update({ skills: [...form.skills, skillInput.trim()] });
      setSkillInput('');
    }
  };

  const addCompany = () => {
    if (companyInput.trim() && !form.targetCompanies.includes(companyInput.trim())) {
      const companies = [...form.targetCompanies, companyInput.trim()];
      update({
        targetCompanies: companies,
        careerGoals: { ...form.careerGoals, targetCompanies: companies },
      });
      setCompanyInput('');
    }
  };

  const profileScore = Math.min(
    100,
    (form.name ? 20 : 0) +
      (form.email ? 15 : 0) +
      (form.college ? 15 : 0) +
      form.skills.length * 5 +
      form.targetCompanies.length * 4 +
      (form.resumeFileName ? 15 : 0),
  );

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await submitOnboarding(form);
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      const guestForm: OnboardingPayload = {
        name: 'Guest User',
        email: `guest_${Date.now()}@college.edu`,
        college: 'Guest Institute',
        branch: 'Computer Science',
        graduationYear: 2026,
        skills: ['Python', 'React', 'TypeScript', 'Node.js'],
        targetCompanies: ['Google', 'Microsoft', 'Amazon'],
        careerGoals: {
          preferredRoles: ['Software Engineer', 'Backend Developer'],
          targetCompanies: ['Google', 'Microsoft', 'Amazon'],
          workPreference: 'hybrid',
          locations: ['Bangalore', 'Remote'],
          workModes: ['Hybrid', 'Remote'],
          employmentTypes: ['Full-time'],
          companyTypes: ['MNC', 'Startup', 'FAANG'],
          requiredConstraints: [],
          salaryExpectation: '12-18 LPA',
        },
      };
      await submitOnboarding(guestForm);
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto grid min-h-screen max-w-6xl lg:grid-cols-2">
        <div className="flex flex-col px-6 py-10 sm:px-10">
          <div className="mb-10">
            <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-md bg-slate-100 text-xs font-bold text-slate-950">
              PC
            </div>
            <h1 className="mt-6 text-2xl font-semibold tracking-tight sm:text-3xl">
              Your AI Placement Officer
            </h1>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-400">
              AI-powered placement guidance, resume optimization, interview preparation and career strategy.
            </p>
          </div>

          <div className="mb-8 flex gap-2">
            {STEPS.map((label, i) => (
              <div key={label} className="flex-1">
                <div
                  className={cn(
                    'mb-2 h-1 rounded-full transition-colors',
                    i <= step ? 'bg-slate-300' : 'bg-slate-800',
                  )}
                />
                <p className={cn('text-[10px]', i <= step ? 'text-slate-300' : 'text-slate-600')}>
                  {label}
                </p>
              </div>
            ))}
          </div>

          <div className="flex-1 space-y-4">
            {step === 0 && (
              <>
                <Field label="Full name">
                  <Input value={form.name} onChange={(e) => update({ name: e.target.value })} placeholder="Priya Sharma" />
                </Field>
                <Field label="Email">
                  <Input value={form.email} onChange={(e) => update({ email: e.target.value })} placeholder="you@college.edu" type="email" />
                </Field>
                <Field label="College">
                  <Input value={form.college} onChange={(e) => update({ college: e.target.value })} placeholder="IIT Delhi" />
                </Field>
                <Field label="Branch">
                  <Input value={form.branch} onChange={(e) => update({ branch: e.target.value })} />
                </Field>
                <Field label="Graduation year">
                  <Input
                    type="number"
                    value={form.graduationYear}
                    onChange={(e) => update({ graduationYear: Number(e.target.value) })}
                  />
                </Field>
              </>
            )}

            {step === 1 && (
              <>
                <Field label="Add skills">
                  <div className="flex gap-2">
                    <Input
                      value={skillInput}
                      onChange={(e) => setSkillInput(e.target.value)}
                      placeholder="Python, React..."
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                    />
                    <Button type="button" variant="outline" onClick={addSkill}>Add</Button>
                  </div>
                </Field>
                <div className="flex flex-wrap gap-2">
                  {form.skills.map((skill) => (
                    <Badge key={skill}>{skill}</Badge>
                  ))}
                </div>
              </>
            )}

            {step === 2 && (
              <>
                <Field label="Target companies">
                  <div className="flex gap-2">
                    <Input
                      value={companyInput}
                      onChange={(e) => setCompanyInput(e.target.value)}
                      placeholder="Google, Stripe..."
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCompany())}
                    />
                    <Button type="button" variant="outline" onClick={addCompany}>Add</Button>
                  </div>
                </Field>
                <div className="flex flex-wrap gap-2">
                  {form.targetCompanies.map((c) => (
                    <Badge key={c}>{c}</Badge>
                  ))}
                </div>
              </>
            )}

            {step === 3 && (
              <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/30 p-8 text-center">
                <Upload className="mx-auto mb-4 h-8 w-8 text-slate-500" />
                <p className="text-sm text-slate-300">Upload your resume (PDF)</p>
                <p className="mt-1 text-xs text-slate-500">Used for ATS analysis and job matching</p>
                <label className="mt-4 inline-block cursor-pointer">
                  <input
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={(e) =>
                      update({ resumeFileName: e.target.files?.[0]?.name ?? undefined })
                    }
                  />
                  <span className="inline-flex h-8 items-center rounded-lg border border-slate-700 px-3 text-sm text-slate-300 hover:border-slate-600">
                    Choose file
                  </span>
                </label>
                {form.resumeFileName && (
                  <p className="mt-3 text-xs text-emerald-400">{form.resumeFileName}</p>
                )}
              </div>
            )}

            {step === 4 && (
              <div className="space-y-6">
                <Field label="Preferred roles (comma separated)">
                  <Input
                    placeholder="Backend Engineer, Full Stack"
                    value={form.careerGoals.preferredRoles.join(', ')}
                    onChange={(e) =>
                      update({
                        careerGoals: {
                          ...form.careerGoals,
                          preferredRoles: e.target.value.split(',').map((r) => r.trim()).filter(Boolean),
                        },
                      })
                    }
                  />
                </Field>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Locations (comma separated)</label>
                    <Input
                      placeholder="Bangalore, Pune, Remote"
                      value={form.careerGoals.locations.join(', ')}
                      onChange={(e) =>
                        update({
                          careerGoals: {
                            ...form.careerGoals,
                            locations: e.target.value.split(',').map((l) => l.trim()).filter(Boolean),
                          }
                        })
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Work Modes</label>
                    <div className="flex flex-wrap gap-2">
                      {['Remote', 'Hybrid', 'On-site'].map((mode) => {
                        const isSelected = form.careerGoals.workModes.includes(mode);
                        return (
                          <Badge 
                            key={mode} 
                            variant={isSelected ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => {
                              const newModes = isSelected 
                                ? form.careerGoals.workModes.filter(m => m !== mode)
                                : [...form.careerGoals.workModes, mode];
                              update({ careerGoals: { ...form.careerGoals, workModes: newModes } });
                            }}
                          >
                            {mode}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Employment Types</label>
                    <div className="flex flex-wrap gap-2">
                      {['Full-time', 'Internship', 'Contract', 'Freelance'].map((type) => {
                        const isSelected = form.careerGoals.employmentTypes.includes(type);
                        return (
                          <Badge 
                            key={type} 
                            variant={isSelected ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => {
                              const newTypes = isSelected 
                                ? form.careerGoals.employmentTypes.filter(t => t !== type)
                                : [...form.careerGoals.employmentTypes, type];
                              update({ careerGoals: { ...form.careerGoals, employmentTypes: newTypes } });
                            }}
                          >
                            {type}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Company Types</label>
                    <div className="flex flex-wrap gap-2">
                      {['Startup', 'MNC', 'Product-based', 'Service-based', 'Fintech', 'FAANG'].map((type) => {
                        const isSelected = form.careerGoals.companyTypes.includes(type);
                        return (
                          <Badge 
                            key={type} 
                            variant={isSelected ? 'default' : 'outline'}
                            className="cursor-pointer"
                            onClick={() => {
                              const newTypes = isSelected 
                                ? form.careerGoals.companyTypes.filter(t => t !== type)
                                : [...form.careerGoals.companyTypes, type];
                              update({ careerGoals: { ...form.careerGoals, companyTypes: newTypes } });
                            }}
                          >
                            {type}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Required Constraints (e.g. Visa Sponsorship, No Relocation)</label>
                    <Input
                      placeholder="Sponsorship required..."
                      value={form.careerGoals.requiredConstraints.join(', ')}
                      onChange={(e) =>
                        update({
                          careerGoals: {
                            ...form.careerGoals,
                            requiredConstraints: e.target.value.split(',').map((c) => c.trim()).filter(Boolean),
                          }
                        })
                      }
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-8 flex items-center justify-between border-t border-slate-800 pt-6">
            <div className="flex gap-2">
              <Button
                type="button"
                variant="ghost"
                disabled={step === 0}
                onClick={() => setStep((s) => s - 1)}
              >
                <ArrowLeft className="mr-1 h-4 w-4" />
                Back
              </Button>
              <Button
                type="button"
                variant="outline"
                className="border-slate-700 text-slate-300"
                onClick={handleGuestLogin}
                disabled={loading}
              >
                Guest Login
              </Button>
            </div>
            {step < STEPS.length - 1 ? (
              <Button type="button" onClick={() => setStep((s) => s + 1)}>
                Continue
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            ) : (
              <Button type="button" onClick={handleSubmit} disabled={loading}>
                {loading ? 'Setting up...' : 'Launch dashboard'}
                <Check className="ml-1 h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        <div className="hidden border-l border-slate-800 bg-slate-900/20 p-10 lg:flex lg:flex-col lg:justify-center">
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
            Live AI profile preview
          </p>
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">{form.name || 'Your name'}</h3>
                <p className="text-sm text-slate-400">{form.college || 'College'} · {form.branch}</p>
              </div>
              <ProgressRing value={profileScore} size={72} />
            </div>
            <div className="space-y-4">
              <PreviewSection title="Skills" items={form.skills} empty="Add your skills" />
              <PreviewSection title="Target companies" items={form.targetCompanies} empty="Add companies" />
              <PreviewSection
                title="Goals"
                items={form.careerGoals.preferredRoles}
                empty="Set career goals"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-2">
      <span className="text-xs font-medium text-slate-400">{label}</span>
      {children}
    </label>
  );
}

function PreviewSection({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div>
      <p className="mb-2 text-xs text-slate-500">{title}</p>
      {items.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item) => (
            <Badge key={item} variant="outline">{item}</Badge>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-600">{empty}</p>
      )}
    </div>
  );
}

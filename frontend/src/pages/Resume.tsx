import { useRef, useState } from 'react';
import { Check, FileText, Upload, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AIInsightCard } from '@/components/shared/AIInsightCard';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingState } from '@/components/shared/LoadingState';
import { PageHeader } from '@/components/shared/PageHeader';
import { ResumeScoreCard } from '@/components/shared/ResumeScoreCard';
import { SectionCard } from '@/components/shared/SectionCard';
import { useResume } from '@/hooks/useQueries';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function ResumePage() {
  const { data, isLoading, isError, refetch } = useResume();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      await api.resume.upload(file);
      // Wait a moment before refetching so backend can process
      setTimeout(() => refetch(), 2000); 
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      setIsUploading(false);
    }
  };


  if (isLoading) return <LoadingState />;
  if (isError || !data || (!data.originalExcerpt && data.scores.overall === 0)) {
    return (
      <EmptyState
        icon={FileText}
        title="No resume analysis"
        description="Upload your resume to get ATS scoring and optimization suggestions."
        action={
          <div className="flex flex-col items-center">
              {isUploading ? (
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500 mb-2" />
              ) : (
                <Button onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
                  Upload Resume PDF
                </Button>
              )}
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept=".pdf" 
                onChange={handleFileUpload} 
              />
          </div>
        }
      />
    );
  }

  const scoreItems = [
    { label: 'ATS Score', value: data.scores.ats },
    { label: 'Keyword Match', value: data.scores.keyword },
    { label: 'Formatting', value: data.scores.formatting },
    { label: 'Impact', value: data.scores.impact },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={data?.targetRole ? `Resume Optimizer · ${data.targetRole}` : "Resume Optimizer"}
        description={
          data?.targetRole
            ? `ATS analysis, keyword optimization, and tailored resume version for ${data.targetRole}${data.targetCompany ? ` at ${data.targetCompany}` : ''}.`
            : "ATS analysis, keyword optimization, and tailored resume versions for your target roles."
        }
      />

      <div className="grid gap-8 lg:grid-cols-[280px_1fr_300px] xl:grid-cols-[300px_1fr_320px]">
        <SectionCard title="Uploaded resume">
          <div className="rounded-lg border border-dashed border-slate-700 p-6 text-center">
            {isUploading ? (
              <Loader2 className="mx-auto mb-3 h-6 w-6 animate-spin text-slate-500" />
            ) : (
              <Upload className="mx-auto mb-3 h-6 w-6 text-slate-500" />
            )}
            <p className="text-sm text-slate-300">
              {isUploading ? "Uploading..." : data?.originalExcerpt ? "Resume uploaded & analyzed" : "No resume found"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {isUploading
                ? "Please wait while AI analyzes it..."
                : data?.targetRole
                ? `Analyzed for ${data.targetRole}`
                : "Upload a PDF to analyze ATS compatibility."}
            </p>
            
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".pdf" 
              onChange={handleFileUpload} 
            />
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-4"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              {data?.originalExcerpt ? "Re-upload Resume" : "Upload PDF"}
            </Button>
          </div>
          <div className="mt-4 space-y-2">
            <p className="text-xs font-medium text-slate-400">
              Missing keywords {data?.targetRole ? `(${data.targetRole})` : ''}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {data.missingKeywords.map((kw) => (
                <Badge key={kw} variant="warning">{kw}</Badge>
              ))}
            </div>
          </div>
        </SectionCard>

        <div className="space-y-6">
          <ResumeScoreCard overall={data.scores.overall} scores={scoreItems} />

          <SectionCard title={`Before / After Comparison · ${data?.targetRole || 'Target Role'}`}>
            <div className="grid gap-4 md:grid-cols-2">
              <ComparisonBlock title="Original Resume (Uploaded)" text={data.originalExcerpt} />
              <ComparisonBlock title={`AI-Optimized for ${data?.targetRole || 'Target Role'}`} text={data.optimizedExcerpt} highlight />
            </div>
          </SectionCard>

          <SectionCard title="Improvement checklist">
            <ul className="space-y-2">
              {data.checklist.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center gap-3 rounded-lg border border-slate-800 px-4 py-3"
                >
                  <div
                    className={cn(
                      'flex h-5 w-5 items-center justify-center rounded border',
                      item.done
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                        : 'border-slate-700 text-slate-600',
                    )}
                  >
                    {item.done && <Check className="h-3 w-3" />}
                  </div>
                  <span className={cn('text-sm', item.done ? 'text-slate-400 line-through' : 'text-slate-200')}>
                    {item.label}
                  </span>
                </li>
              ))}
            </ul>
          </SectionCard>
        </div>

        <SectionCard title="AI recommendations">
          <div className="space-y-3">
            {data.suggestions.map((suggestion, i) => (
              <AIInsightCard
                key={i}
                title={`Suggestion ${i + 1}`}
                description={suggestion}
                type="action"
              />
            ))}
            <div className="rounded-lg border border-slate-800 p-4">
              <p className="mb-2 text-xs font-medium text-slate-400">Present keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {data.presentKeywords.map((kw) => (
                  <Badge key={kw} variant="success">{kw}</Badge>
                ))}
              </div>
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

function ComparisonBlock({ title, text, highlight }: { title: string; text: string; highlight?: boolean }) {
  return (
    <div className={cn('rounded-sm border p-4 flex flex-col', highlight ? 'border-slate-600 bg-slate-800/30' : 'border-slate-800')}>
      <p className="mb-2 text-xs font-medium text-slate-400 shrink-0">{title}</p>
      <div className="max-h-80 overflow-y-auto pr-2 custom-scrollbar">
        <p className="text-sm leading-relaxed text-slate-300 whitespace-pre-wrap break-words">{text}</p>
      </div>
    </div>
  );
}

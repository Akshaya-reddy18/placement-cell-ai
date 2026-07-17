import { useState } from 'react';
import { MessageSquare, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/shared/EmptyState';
import { InterviewCard } from '@/components/shared/InterviewCard';
import { LoadingState } from '@/components/shared/LoadingState';
import { PageHeader } from '@/components/shared/PageHeader';
import { ProgressRing } from '@/components/shared/ProgressRing';
import { SectionCard } from '@/components/shared/SectionCard';
import { MockInterviewModal } from '@/components/shared/MockInterviewModal';
import { Badge } from '@/components/ui/badge';
import { useInterview } from '@/hooks/useQueries';

export default function InterviewPage() {
  const { data, isLoading, isError } = useInterview();
  const [showModal, setShowModal] = useState(false);

  if (isLoading) return <LoadingState />;
  if (isError || !data) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="Interview prep unavailable"
        description="Complete your profile analysis to generate personalized interview questions."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interview Prep"
        description="Practice technical and behavioral questions tailored to your target roles."
        actions={
          <Button variant="outline" size="sm" onClick={() => setShowModal(true)}>
            <Play className="mr-1.5 h-4 w-4" />
            Start mock interview
          </Button>
        }
      />
      {showModal && <MockInterviewModal onClose={() => setShowModal(false)} />}

      <div className="grid gap-4 sm:grid-cols-3">
        <ScorePanel label="Readiness" value={data.readinessScore} />
        <ScorePanel label="Confidence" value={data.confidenceScore} />
        <SectionCard>
          <p className="mb-3 text-xs font-medium text-slate-400">AI Feedback</p>
          <p className="text-sm leading-relaxed text-slate-300">{data.feedback}</p>
        </SectionCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Technical interviews">
          <div className="space-y-3">
            {data.technicalQuestions.map((q) => (
              <InterviewCard key={q.id} question={q} />
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Behavioral interviews">
          <div className="space-y-3">
            {data.behavioralQuestions.map((q) => (
              <InterviewCard key={q.id} question={q} />
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <SectionCard title="Mock sessions">
          <div className="space-y-3">
            {data.mockSessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-3"
              >
                <div>
                  <p className="text-sm text-slate-200">{session.title}</p>
                  <p className="text-xs text-slate-500">{session.date} · {session.questionsCount} questions</p>
                </div>
                <Badge variant="outline">{session.score}%</Badge>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Strong areas">
          <div className="flex flex-wrap gap-2">
            {data.strongAreas.map((area) => (
              <Badge key={area} variant="success">{area}</Badge>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Areas to improve">
          <div className="flex flex-wrap gap-2">
            {data.weakAreas.map((area) => (
              <Badge key={area} variant="warning">{area}</Badge>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

function ScorePanel({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40 p-6">
      <ProgressRing value={value} size={100} label={label} />
    </div>
  );
}

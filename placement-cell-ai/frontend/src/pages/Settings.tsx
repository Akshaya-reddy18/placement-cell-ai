import { Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/shared/PageHeader';
import { SectionCard } from '@/components/shared/SectionCard';
import { useAppStore } from '@/store/useStore';

export default function SettingsPage() {
  const user = useAppStore((s) => s.user);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your profile and platform preferences."
      />

      <SectionCard title="Profile">
        <div className="grid max-w-lg gap-4">
          <Field label="Name" defaultValue={user?.name} />
          <Field label="Email" defaultValue={user?.email} />
          <Field label="College" defaultValue={user?.college} />
          <Field label="Branch" defaultValue={user?.branch} />
          <Button className="w-fit">Save changes</Button>
        </div>
      </SectionCard>

      <SectionCard title="Notifications">
        <p className="text-sm text-slate-400">
          Email alerts for application deadlines, interview reminders, and AI insights.
        </p>
        <Button variant="outline" size="sm" className="mt-4">
          <Settings className="mr-1.5 h-4 w-4" />
          Configure notifications
        </Button>
      </SectionCard>
    </div>
  );
}

function Field({ label, defaultValue }: { label: string; defaultValue?: string }) {
  return (
    <label className="block space-y-2">
      <span className="text-xs font-medium text-slate-400">{label}</span>
      <Input defaultValue={defaultValue} />
    </label>
  );
}

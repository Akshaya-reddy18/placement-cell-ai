import { Badge } from '@/components/ui/badge';

interface StatusBadgeProps {
  status: string;
}

const statusMap: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' | 'outline' }> = {
  running: { label: 'Analyzing', variant: 'warning' },
  completed: { label: 'Ready', variant: 'success' },
  failed: { label: 'Failed', variant: 'danger' },
  idle: { label: 'Idle', variant: 'outline' },
  high: { label: 'High', variant: 'success' },
  medium: { label: 'Medium', variant: 'warning' },
  low: { label: 'Low', variant: 'outline' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusMap[status.toLowerCase()] ?? { label: status, variant: 'default' as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

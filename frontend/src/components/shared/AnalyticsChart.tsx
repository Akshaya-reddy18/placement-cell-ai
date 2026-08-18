import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { cn } from '@/lib/utils';

interface AnalyticsChartProps {
  data: Record<string, string | number>[];
  type?: 'bar' | 'line';
  dataKeys?: string[];
  xKey?: string;
  height?: number;
  className?: string;
}

const COLORS = ['#94a3b8', '#64748b', '#475569'];

export function AnalyticsChart({
  data,
  type = 'bar',
  dataKeys = ['applications', 'interviews'],
  xKey = 'name',
  height = 280,
  className,
}: AnalyticsChartProps) {
  const Chart = type === 'bar' ? BarChart : LineChart;

  return (
    <div className={cn('w-full', className)} style={{ height, minWidth: 0, minHeight: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <Chart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontSize: '12px',
            }}
          />
          {type === 'bar'
            ? dataKeys.map((key, i) => (
                <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
              ))
            : dataKeys.map((key, i) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
        </Chart>
      </ResponsiveContainer>
    </div>
  );
}

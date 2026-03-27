import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import SeverityFilter from '@/components/logs/SeverityFilter';
import LogList from '@/components/logs/LogList';
import { getLogs } from '@/lib/api';
import type { SystemLog } from '@/types/api';

type Severity = 'all' | 'info' | 'warning' | 'error' | 'fatal';

export default function SystemLogs() {
  const [severity, setSeverity] = useState<Severity>('all');
  const [node, setNode] = useState('all');

  const { data: logs = [], isLoading } = useQuery<SystemLog[]>({
    queryKey: ['logs', severity, node],
    queryFn: () => getLogs(
      severity === 'all' ? undefined : severity,
      node === 'all' ? undefined : node,
    ),
    refetchInterval: 5_000,
  });

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">System Logs</h1>
        <p className="text-slate-400 text-sm mt-1">
          {isLoading ? 'Loading...' : `${logs.length} entries`}
        </p>
      </div>
      <SeverityFilter
        severity={severity}
        onSeverityChange={setSeverity}
        node={node}
        onNodeChange={setNode}
      />
      <LogList logs={logs} loading={isLoading} />
    </div>
  );
}

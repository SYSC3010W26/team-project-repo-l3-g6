import { useMemo, useState } from 'react';
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
    queryFn: () =>
      getLogs(
        severity === 'all' ? undefined : severity,
        node === 'all' ? undefined : node,
      ),
    refetchInterval: 5_000,
  });

  const fatalCount = useMemo(() => logs.filter(log => log.severity === 'fatal').length, [logs]);
  const errorCount = useMemo(() => logs.filter(log => log.severity === 'error').length, [logs]);

  return (
    <section className="w-full max-w-none space-y-6" aria-label="Activity Console">
      <header className="rounded-2xl border border-cyan-500/25 bg-slate-950/70 p-6 shadow-[0_0_60px_rgba(34,211,238,0.08)] backdrop-blur-md">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300/80">Kinetic Lab</p>
            <h1 className="font-mono text-2xl font-semibold text-cyan-100">System Activity Console</h1>
            <p className="text-sm text-slate-300/80">
              Live operator feed from scanner, solver, motor, and persistence nodes.
            </p>
          </div>

          <div className="grid min-w-[220px] grid-cols-2 gap-2 text-xs font-mono">
            <div className="rounded-lg border border-slate-700/70 bg-slate-900/70 px-3 py-2">
              <p className="text-slate-400">Entries</p>
              <p className="mt-1 text-cyan-200">{isLoading ? '...' : logs.length}</p>
            </div>
            <div className="rounded-lg border border-red-500/40 bg-red-950/30 px-3 py-2">
              <p className="text-red-300/80">Fatal / Error</p>
              <p className="mt-1 text-red-200">{isLoading ? '...' : `${fatalCount} / ${errorCount}`}</p>
            </div>
          </div>
        </div>
      </header>

      <SeverityFilter
        severity={severity}
        onSeverityChange={setSeverity}
        node={node}
        onNodeChange={setNode}
      />

      <LogList logs={logs} loading={isLoading} />
    </section>
  );
}

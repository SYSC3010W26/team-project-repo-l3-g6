import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import type { NodeStatus, PipelineStatus, SolveSession, CubeState, SystemLog } from '@/types/api';
import { useQuery } from '@tanstack/react-query';
import { getLogs } from '@/lib/api';

interface DashboardLogPanelProps {
  loading: boolean;
  latestSession?: SolveSession;
  status: PipelineStatus;
  nodes: NodeStatus[];
  scanData?: CubeState;
}

function formatSessionTimestamp(value: string | null | undefined): string {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '--';
  return date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function DashboardLogPanel({
  loading,
  latestSession,
  status,
  nodes,
  scanData,
}: DashboardLogPanelProps) {
  const { data: logs, isLoading: logsLoading } = useQuery<SystemLog[]>({
    queryKey: ['logs'],
    queryFn: () => getLogs(),
    refetchInterval: 3000,
  });

  if (loading || logsLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5, 6].map((index) => (
          <Skeleton key={index} className="h-6 w-full rounded-md bg-kl-surface-high" />
        ))}
      </div>
    );
  }

  const hasSession = Boolean(latestSession);
  const sessionId = latestSession?.session_id;

  // Filter logs for current session if active, otherwise show last few global logs
  const displayLogs = logs?.filter(log => !sessionId || log.session_id === sessionId) ?? [];

  return (
    <div className="rounded-xl border border-kl-outline-variant bg-kl-surface-lowest/70 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-kl-on-surface-variant">Activity Console</p>
        <span className="rounded border border-kl-outline-variant px-2 py-0.5 font-mono text-[10px] text-kl-on-surface-variant">
          {hasSession ? 'live' : 'idle'}
        </span>
      </div>

      <ScrollArea className="h-56 rounded border border-kl-outline-variant bg-black/40 p-2">
        <div className="space-y-1 font-mono text-xs text-kl-on-surface">
          {displayLogs.length > 0 ? (
            displayLogs.map((log) => (
              <p key={log.id} className="break-words text-kl-on-surface-variant">
                <span className="text-kl-secondary">[{formatSessionTimestamp(log.created_at)}]</span>
                {log.node_id && <span className="text-blue-400"> [{log.node_id}]</span>}
                <span className={log.severity === 'error' ? 'text-red-400' : log.severity === 'warning' ? 'text-yellow-400' : 'text-kl-on-surface'}>
                  {' '}{log.message}
                </span>
              </p>
            ))
          ) : (
            <p className="text-kl-on-surface-variant italic">
              <span className="text-kl-secondary">$</span> [idle] waiting for system events...
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

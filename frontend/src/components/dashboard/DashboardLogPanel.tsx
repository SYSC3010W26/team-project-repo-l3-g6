import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import type { NodeStatus, PipelineStatus, SolveSession, CubeState } from '@/types/api';

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
  return date.toLocaleTimeString();
}

export default function DashboardLogPanel({
  loading,
  latestSession,
  status,
  nodes,
  scanData,
}: DashboardLogPanelProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5, 6].map((index) => (
          <Skeleton key={index} className="h-6 w-full rounded-md bg-kl-surface-high" />
        ))}
      </div>
    );
  }

  const hasSession = Boolean(latestSession);
  const totalNodes = nodes.length;
  const onlineNodes = nodes.filter((node) => node.is_online).length;

  const idleLines = [
    '[idle] waiting for next solve request',
    `[idle] cluster heartbeat ${onlineNodes}/${totalNodes || 4} nodes online`,
    '[idle] terminal will stream session events once execution starts',
  ];

  const liveLines = [
    `[session:${latestSession?.session_id}] status=${status}`,
    `[session:${latestSession?.session_id}] algorithm=${latestSession?.selected_algorithm ?? 'unknown'}`,
    `[session:${latestSession?.session_id}] started_at=${formatSessionTimestamp(latestSession?.started_at)}`,
    `[session:${latestSession?.session_id}] completed_at=${formatSessionTimestamp(latestSession?.completed_at)}`,
    `[scan] state_string=${scanData?.state_string ? 'present' : 'pending'}`,
    `[scan] confidence=${scanData?.confidence ?? '--'}`,
    `[nodes] online=${onlineNodes}/${totalNodes || 4}`,
  ];

  const lines = hasSession ? liveLines : idleLines;

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
          {lines.map((line) => (
            <p key={line} className="break-words text-kl-on-surface-variant">
              <span className="text-kl-secondary">$</span> {line}
            </p>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

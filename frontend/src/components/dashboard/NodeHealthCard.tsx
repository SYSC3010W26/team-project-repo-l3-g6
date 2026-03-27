import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { NodeStatus } from '@/types/api';

interface Props {
  node: NodeStatus | undefined;
  nodeName: string;
  loading?: boolean;
}

function formatHeartbeat(heartbeat?: string | null) {
  if (!heartbeat) return 'No heartbeat observed yet';
  const timestamp = new Date(heartbeat);
  if (Number.isNaN(timestamp.getTime())) return 'Heartbeat timestamp unavailable';

  return `${timestamp.toLocaleTimeString()} • ${timestamp.toLocaleDateString()}`;
}

function heartbeatAgeLabel(heartbeat?: string | null) {
  if (!heartbeat) return 'Awaiting first signal';
  const ts = new Date(heartbeat);
  if (Number.isNaN(ts.getTime())) return 'Timestamp unreadable';

  const deltaSeconds = Math.max(0, Math.floor((Date.now() - ts.getTime()) / 1000));
  if (deltaSeconds < 5) return 'Updated just now';
  if (deltaSeconds < 60) return `${deltaSeconds}s ago`;
  const minutes = Math.floor(deltaSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function NodeHealthCard({ node, nodeName, loading }: Props) {
  if (loading) return <Skeleton className="h-36 rounded-2xl bg-kl-surface-high" />;

  const online = node?.is_online ?? false;
  const heartbeatDisplay = formatHeartbeat(node?.last_heartbeat);
  const heartbeatAge = heartbeatAgeLabel(node?.last_heartbeat);

  return (
    <Card className="glass border-kl-outline-variant/45 bg-kl-surface-low/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-sm font-semibold text-kl-on-surface">{nodeName}</CardTitle>
            <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-kl-on-surface-variant">Node health</p>
          </div>
          <Badge
            variant="outline"
            className={online
              ? 'border-emerald-500/45 bg-emerald-500/15 text-emerald-300'
              : 'border-red-500/45 bg-red-500/15 text-red-300'}
          >
            <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current" />
            {online ? 'Online' : 'Offline'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="rounded-xl border border-kl-outline-variant/45 bg-kl-surface-low/70 px-3 py-2.5">
          <p className="text-[11px] uppercase tracking-[0.18em] text-kl-on-surface-variant">Last heartbeat</p>
          <p className="mt-1 text-xs font-medium text-kl-on-surface">{heartbeatDisplay}</p>
          <p className="mt-1 text-[11px] text-kl-on-surface-variant">{heartbeatAge}</p>
        </div>
      </CardContent>
    </Card>
  );
}

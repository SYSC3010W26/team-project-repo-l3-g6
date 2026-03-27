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

export default function NodeHealthCard({ node, nodeName, loading }: Props) {
  if (loading) return <Skeleton className="h-28 rounded-2xl bg-kl-surface-high" />;

  const online = node?.is_online ?? false;
  const heartbeatDisplay = formatHeartbeat(node?.last_heartbeat);

  return (
    <Card className="glass border-kl-outline-variant/60 shadow-none">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-sm font-medium text-kl-on-surface">{nodeName}</CardTitle>
          <Badge
            variant="outline"
            className={online
              ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300'
              : 'border-red-500/40 bg-red-500/15 text-red-300'}
          >
            <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current" />
            {online ? 'Online' : 'Offline'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="rounded-lg border border-kl-outline-variant/50 bg-kl-surface-low/60 px-3 py-2">
          <p className="text-[11px] uppercase tracking-[0.18em] text-kl-on-surface-variant">Last heartbeat</p>
          <p className="mt-1 text-xs font-medium text-kl-on-surface">{heartbeatDisplay}</p>
        </div>
      </CardContent>
    </Card>
  );
}

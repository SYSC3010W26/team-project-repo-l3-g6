import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { NodeStatus } from '@/types/api';

interface Props {
  node: NodeStatus | undefined;
  nodeName: string;
  loading?: boolean;
}

export default function NodeHealthCard({ node, nodeName, loading }: Props) {
  if (loading) return <Skeleton className="h-24 rounded-lg" />;
  const online = node?.is_online ?? false;
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-300">{nodeName}</CardTitle>
      </CardHeader>
      <CardContent>
        <Badge
          variant={online ? 'default' : 'destructive'}
          className={online ? 'bg-green-500/20 text-green-400 border-green-500/30' : ''}
        >
          {online ? 'Online' : 'Offline'}
        </Badge>
        {node?.last_heartbeat && (
          <p className="text-xs text-slate-500 mt-2">
            Last seen: {new Date(node.last_heartbeat).toLocaleTimeString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

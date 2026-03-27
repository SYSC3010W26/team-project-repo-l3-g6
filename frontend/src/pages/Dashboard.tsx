import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import PipelineStepper from '@/components/dashboard/PipelineStepper';
import NodeHealthCard from '@/components/dashboard/NodeHealthCard';
import ControlButtons from '@/components/dashboard/ControlButtons';
import { getAllNodes, getSessions, startSolve, postControlFlag } from '@/lib/api';
import { useSocketEvent } from '@/hooks/useSocket';
import type { PipelineStatus, NodeStatus } from '@/types/api';

const NODE_DISPLAY_NAMES: Record<string, string> = {
  scanner: 'Scanner Pi',
  solver: 'Solver Pi',
  motor: 'Motor Pi',
  database: 'Database Pi',
};

export default function Dashboard() {
  const queryClient = useQueryClient();

  const { data: nodes, isLoading: nodesLoading } = useQuery<NodeStatus[]>({
    queryKey: ['nodes'],
    queryFn: getAllNodes,
    refetchInterval: 5_000,
  });

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: getSessions,
    refetchInterval: 10_000,
  });

  const latestSession = sessions?.[0];
  const status: PipelineStatus = latestSession?.status ?? 'idle';
  const sessionId = latestSession?.id ?? null;

  useSocketEvent('job_state_update', () => {
    queryClient.invalidateQueries({ queryKey: ['sessions'] });
    queryClient.invalidateQueries({ queryKey: ['nodes'] });
  });

  const { mutate: doStart, isPending: starting } = useMutation({
    mutationFn: startSolve,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sessions'] }),
  });

  const { mutate: doControl, isPending: controlling } = useMutation({
    mutationFn: ({ action }: { action: string }) =>
      postControlFlag(sessionId!, action),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sessions'] }),
  });

  function handleAction(action: string) {
    if (action === 'start') { doStart(); return; }
    if (sessionId) doControl({ action });
  }

  const nodeList = ['scanner', 'solver', 'motor', 'database'];
  const nodeMap = Object.fromEntries((nodes ?? []).map((n) => [n.node_id, n]));

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Real-time overview of the solve pipeline</p>
      </div>

      {/* Pipeline Stage */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-slate-400 font-medium uppercase tracking-wide">
            Pipeline Stage
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <Skeleton className="h-12 w-full" />
          ) : (
            <PipelineStepper status={status} />
          )}
        </CardContent>
      </Card>

      {/* Node Health */}
      <div>
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide mb-3">
          Node Health
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {nodeList.map((nodeId) => (
            <NodeHealthCard
              key={nodeId}
              node={nodeMap[nodeId]}
              nodeName={NODE_DISPLAY_NAMES[nodeId]}
              loading={nodesLoading}
            />
          ))}
        </div>
      </div>

      {/* Active Job */}
      {latestSession && (
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400 font-medium uppercase tracking-wide">
              Active Session
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4">
            <Badge variant="outline" className="font-mono text-xs text-slate-300 border-slate-700">
              {latestSession.id}
            </Badge>
            <Badge className={
              status === 'error' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
              status === 'done' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
              'bg-blue-500/20 text-blue-400 border-blue-500/30'
            }>
              {status}
            </Badge>
          </CardContent>
        </Card>
      )}

      {/* Control Buttons */}
      <div>
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide mb-3">
          Controls
        </h2>
        {sessionsLoading ? (
          <div className="flex gap-3">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-10 w-24" />)}
          </div>
        ) : (
          <ControlButtons
            status={status}
            sessionId={sessionId}
            onAction={handleAction}
            loading={starting || controlling}
          />
        )}
      </div>
    </div>
  );
}

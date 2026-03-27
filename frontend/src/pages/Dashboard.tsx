import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import PipelineStepper from '@/components/dashboard/PipelineStepper';
import NodeHealthCard from '@/components/dashboard/NodeHealthCard';
import ControlButtons from '@/components/dashboard/ControlButtons';
import CubeViewer3D from '@/components/dashboard/CubeViewer3D';
import DashboardLogPanel from '@/components/dashboard/DashboardLogPanel';
import { getAllNodes, getSessions, startSolve, postControlFlag, getScanState } from '@/lib/api';
import { useSocketEvent } from '@/hooks/useSocket';
import type { PipelineStatus, NodeStatus, CubeState } from '@/types/api';

const NODE_DISPLAY_NAMES: Record<string, string> = {
  scanner: 'Scanner Pi',
  solver: 'Solver Pi',
  motor: 'Motor Pi',
  database: 'Database Pi',
};

function statusBadgeClass(status: PipelineStatus): string {
  if (status === 'error') return 'bg-red-500/20 text-red-400 border-red-500/30';
  if (status === 'done') return 'bg-green-500/20 text-green-400 border-green-500/30';
  if (status === 'idle') return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
}

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
  const sessionId = latestSession?.session_id ?? null;

  const { data: scanData, isLoading: scanLoading } = useQuery<CubeState>({
    queryKey: ['scan', sessionId],
    queryFn: () => getScanState(sessionId!),
    enabled: !!sessionId,
  });

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
    if (action === 'start') {
      doStart();
      return;
    }
    if (sessionId) doControl({ action });
  }

  const nodeList = ['scanner', 'solver', 'motor', 'database'];
  const nodeMap = Object.fromEntries((nodes ?? []).map((n) => [n.node_id, n]));

  const progressPercent =
    status === 'idle' ? 0 : status === 'scanning' ? 25 : status === 'solving' ? 55 : status === 'executing' ? 80 : 100;

  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-kl-outline-variant bg-kl-surface-low p-5 md:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-kl-on-surface-variant">Kinetic Lab Console</p>
            <h1 className="mt-2 text-2xl font-semibold text-kl-on-surface md:text-3xl">Active Session</h1>
            <p className="mt-2 text-sm text-kl-on-surface-variant">
              Real-time pipeline monitoring, node status, and execution activity for the current solve.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <Badge variant="outline" className="border-kl-outline-variant font-mono text-xs text-kl-on-surface-variant">
              {latestSession ? `#${latestSession.session_id}` : '#--'}
            </Badge>
            <Badge className={statusBadgeClass(status)}>{status}</Badge>
          </div>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <Card className="glass border-kl-outline-variant xl:col-span-7">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-kl-on-surface-variant">
              Pipeline Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {sessionsLoading ? <Skeleton className="h-24 w-full rounded-xl bg-kl-surface-high" /> : <PipelineStepper status={status} />}
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-kl-on-surface-variant">
                <span>Session completion</span>
                <span className="font-medium text-kl-on-surface">{progressPercent}%</span>
              </div>
              <div className="h-2.5 rounded-full bg-kl-surface-high">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-kl-primary/80 via-kl-primary to-cyan-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-kl-outline-variant xl:col-span-5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-kl-on-surface-variant">
              Session Snapshot
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="text-kl-on-surface-variant">
              Algorithm:{' '}
              <span className="font-medium text-kl-on-surface">{latestSession?.selected_algorithm ?? 'Waiting for run'}</span>
            </p>
            <p className="text-kl-on-surface-variant">
              Started:{' '}
              <span className="font-medium text-kl-on-surface">
                {latestSession?.started_at ? new Date(latestSession.started_at).toLocaleTimeString() : '--'}
              </span>
            </p>
            <p className="text-kl-on-surface-variant">
              Completed:{' '}
              <span className="font-medium text-kl-on-surface">
                {latestSession?.completed_at ? new Date(latestSession.completed_at).toLocaleTimeString() : '--'}
              </span>
            </p>
          </CardContent>
        </Card>

        <Card className="glass border-kl-outline-variant xl:col-span-8">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-kl-on-surface-variant">
              Cube Viewer
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 px-4 pb-4">
            {scanLoading ? <Skeleton className="h-[300px] w-full bg-kl-surface-high" /> : <CubeViewer3D stateString={scanData?.state_string} />}
          </CardContent>
        </Card>

        <Card className="glass border-kl-outline-variant xl:col-span-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-kl-on-surface-variant">
              Controls
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sessionsLoading ? (
              <div className="flex flex-wrap gap-3">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-10 w-24 bg-kl-surface-high" />
                ))}
              </div>
            ) : (
              <ControlButtons
                status={status}
                sessionId={sessionId}
                onAction={handleAction}
                loading={starting || controlling}
              />
            )}
          </CardContent>
        </Card>

        <div className="xl:col-span-8">
          <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-kl-on-surface-variant">Node Health</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
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

        <Card className="glass border-kl-outline-variant xl:col-span-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-kl-on-surface-variant">
              Activity Terminal
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DashboardLogPanel
              loading={sessionsLoading}
              latestSession={latestSession}
              status={status}
              nodes={nodes ?? []}
              scanData={scanData}
            />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

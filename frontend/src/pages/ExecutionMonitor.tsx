import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import ProgressHeader from '@/components/execution/ProgressHeader';
import MoveProgressList from '@/components/execution/MoveProgressList';
import { useSocketEvent } from '@/hooks/useSocket';
import { getSessions, getSolution } from '@/lib/api';
import type { ExecutionProgressUpdate } from '@/types/api';

export default function ExecutionMonitor() {
  const queryClient = useQueryClient();
  const [liveProgress, setLiveProgress] = useState<ExecutionProgressUpdate | null>(null);

  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions'],
    queryFn: getSessions,
    refetchInterval: 10_000,
  });

  const activeSession = sessions.find((s: any) => s.status === 'executing');
  const sessionId = activeSession?.session_id ?? null;

  const { data: solution } = useQuery({
    queryKey: ['solution', sessionId],
    queryFn: () => getSolution(sessionId!),
    enabled: !!sessionId,
  });

  useSocketEvent('execution_progress', (data) => {
    setLiveProgress(data);
    queryClient.invalidateQueries({ queryKey: ['sessions'] });
  });

  const allMoves = (solution?.steps ?? []).map((s: any) => ({
    index: s.step_index,
    notation: s.move_notation,
  }));

  const currentStep = liveProgress?.current_step ?? 0;
  const isComplete = liveProgress && liveProgress.pct_complete >= 1.0;

  if (!activeSession && !liveProgress) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.22em] text-kl-secondary">KINETIC LAB</p>
          <h1 className="font-space-grotesk text-3xl font-semibold text-kl-on-surface">Execution Monitor</h1>
        </div>

        <Card className="glass border-kl-outline-variant/70 bg-kl-surface-low/40">
          <CardContent className="py-14 text-center">
            <p className="font-space-grotesk text-xl text-kl-on-surface">No active solve</p>
            <p className="mt-1 text-sm text-kl-on-surface-variant">Start a solve to track motor progress.</p>
            <Link to="/">
              <Button variant="outline" className="mt-5 border-kl-outline-variant text-kl-on-surface-variant hover:bg-kl-surface-high">
                Go to Dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-2">
        <p className="text-xs uppercase tracking-[0.22em] text-kl-secondary">KINETIC LAB</p>
        <h1 className="font-space-grotesk text-3xl font-semibold text-kl-on-surface">Execution Monitor</h1>
        {sessionId && <p className="font-mono text-xs text-kl-on-surface-variant">Session #{sessionId}</p>}
      </div>

      {isComplete && (
        <div className="rounded-xl border border-emerald-400/30 bg-emerald-500/[0.08] px-4 py-3">
          <p className="font-medium text-emerald-300">Execution complete</p>
        </div>
      )}

      <Card className="glass border-kl-outline-variant/70 bg-kl-surface-low/45">
        <CardContent className="p-4 sm:p-5">
          <p className="mb-3 text-xs uppercase tracking-[0.2em] text-kl-primary">Progress</p>
          <ProgressHeader progress={liveProgress} />
        </CardContent>
      </Card>

      {allMoves.length > 0 && (
        <section className="space-y-3">
          <p className="text-xs uppercase tracking-[0.2em] text-kl-primary">Move Sequence</p>
          <MoveProgressList moves={allMoves} currentStep={currentStep} />
        </section>
      )}
    </div>
  );
}

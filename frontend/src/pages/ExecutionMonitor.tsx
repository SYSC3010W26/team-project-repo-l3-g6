import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

  // Real-time execution progress via Socket.IO
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
      <div className="space-y-4 max-w-2xl">
        <h1 className="text-2xl font-bold text-white">Execution Monitor</h1>
        <div className="text-center py-16 border border-slate-800 rounded-lg bg-slate-900/30">
          <p className="text-slate-400 font-medium">No active solve</p>
          <p className="text-slate-500 text-sm mt-1">Start a solve to track motor progress.</p>
          <Link to="/">
            <Button variant="outline" className="mt-4 border-slate-700 text-slate-300">
              Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Execution Monitor</h1>
        {sessionId && (
          <p className="text-slate-400 text-sm mt-1 font-mono">
            Session #{sessionId}
          </p>
        )}
      </div>

      {isComplete && (
        <div className="rounded-lg bg-green-500/10 border border-green-500/30 px-4 py-3">
          <p className="text-green-400 font-medium">✓ Execution complete</p>
        </div>
      )}

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-slate-400 font-medium uppercase tracking-wide">
            Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ProgressHeader progress={liveProgress} />
        </CardContent>
      </Card>

      {allMoves.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide mb-3">
            Move Sequence
          </h2>
          <MoveProgressList moves={allMoves} currentStep={currentStep} />
        </div>
      )}
    </div>
  );
}

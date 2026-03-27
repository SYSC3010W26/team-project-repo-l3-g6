import { useQuery } from '@tanstack/react-query';
import SessionTable from '@/components/results/SessionTable';
import { getSessions } from '@/lib/api';
import type { SolveSession } from '@/types/api';

export default function SolveResults() {
  const { data: sessions = [], isLoading } = useQuery<SolveSession[]>({
    queryKey: ['sessions'],
    queryFn: getSessions,
    refetchInterval: 10_000,
  });

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Solve History</h1>
        <p className="text-slate-400 text-sm mt-1">
          {sessions.length > 0
            ? `${sessions.length} session${sessions.length === 1 ? '' : 's'} recorded`
            : 'No sessions yet'}
        </p>
      </div>
      <SessionTable sessions={sessions} loading={isLoading} />
    </div>
  );
}

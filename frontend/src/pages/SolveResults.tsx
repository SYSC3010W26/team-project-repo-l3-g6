import { useQuery } from '@tanstack/react-query';
import { Skeleton } from '@/components/ui/skeleton';
import SuccessCard from '@/components/results/SuccessCard';
import { getSessions } from '@/lib/api';
import type { SolveSession } from '@/types/api';

export default function SolveResults() {
  const { data: sessions = [], isLoading } = useQuery<SolveSession[]>({
    queryKey: ['sessions'],
    queryFn: getSessions,
    refetchInterval: 10_000,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/10 via-white/5 to-slate-900/50 p-6 backdrop-blur-xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-cyan-300/80">Kinetic Lab</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Solve Results</h1>
        <p className="mt-2 text-sm text-slate-300">
          Review recent solve sessions, inspect outcomes, and open any run for full step-by-step playback.
        </p>
        <p className="mt-4 text-xs text-slate-400">
          {sessions.length > 0
            ? `${sessions.length} session${sessions.length === 1 ? '' : 's'} tracked`
            : 'No sessions recorded yet'}
        </p>
      </header>

      {isLoading ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Loading solve sessions">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-[228px] rounded-2xl border border-white/10 bg-white/5" />
          ))}
        </section>
      ) : sessions.length === 0 ? (
        <section className="rounded-2xl border border-dashed border-white/20 bg-slate-950/40 p-14 text-center backdrop-blur-md">
          <p className="text-lg font-medium text-slate-100">No solve sessions yet</p>
          <p className="mt-2 text-sm text-slate-400">
            Start a solve from the dashboard to populate this gallery.
          </p>
        </section>
      ) : (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Solve session gallery">
          {sessions.map((session) => (
            <SuccessCard key={session.session_id} session={session} />
          ))}
        </section>
      )}
    </div>
  );
}

import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import type { SolveSession } from '@/types/api';

interface SuccessCardProps {
  session: SolveSession;
}

function getStatusStyles(status: string) {
  const normalized = status.toLowerCase();

  if (normalized === 'done') {
    return 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300';
  }

  if (normalized === 'executing') {
    return 'border-sky-400/40 bg-sky-400/10 text-sky-300';
  }

  if (normalized === 'error') {
    return 'border-rose-400/40 bg-rose-400/10 text-rose-300';
  }

  return 'border-slate-400/30 bg-slate-400/10 text-slate-300';
}

function formatTimestamp(value: string | null) {
  if (!value) return '—';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';

  return date.toLocaleString();
}

export default function SuccessCard({ session }: SuccessCardProps) {
  const navigate = useNavigate();

  return (
    <button
      type="button"
      onClick={() => navigate(`/review/${session.session_id}`)}
      className="group relative w-full overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-white/12 via-white/8 to-white/5 p-5 text-left shadow-[0_22px_50px_-24px_rgba(2,8,23,0.85)] backdrop-blur-xl transition duration-200 hover:-translate-y-0.5 hover:border-cyan-300/40 hover:shadow-[0_24px_54px_-20px_rgba(34,211,238,0.35)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70"
      aria-label={`Open review for session ${session.session_id}`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.16),_transparent_58%)] opacity-70 transition-opacity group-hover:opacity-100" />
      <div className="relative z-10 space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-400">
              Session #{session.session_id}
            </p>
            <h3 className="line-clamp-2 text-base font-semibold text-white">
              {session.session_name ?? 'Untitled Solve Session'}
            </h3>
          </div>
          <Badge className={getStatusStyles(session.status)}>{session.status}</Badge>
        </div>

        <div className="grid gap-3 rounded-xl border border-white/10 bg-slate-950/35 p-3 sm:grid-cols-2">
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-slate-400">Algorithm</p>
            <p className="mt-1 text-sm font-medium text-slate-200">
              {session.selected_algorithm ?? '—'}
            </p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-slate-400">Completed</p>
            <p className="mt-1 text-sm font-medium text-slate-200">
              {formatTimestamp(session.completed_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Started {formatTimestamp(session.started_at)}</span>
          <span className="text-cyan-300 transition-colors group-hover:text-cyan-200">Open review →</span>
        </div>
      </div>
    </button>
  );
}

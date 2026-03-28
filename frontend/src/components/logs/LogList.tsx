import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import type { SystemLog } from '@/types/api';

interface Props {
  logs: SystemLog[];
  loading: boolean;
}

const SEVERITY_TONE: Record<string, string> = {
  info: 'text-slate-200 border-slate-500/40 bg-slate-700/20',
  warning: 'text-amber-100 border-amber-400/50 bg-amber-500/15',
  error: 'text-red-100 border-red-400/60 bg-red-500/20',
  fatal: 'text-red-50 border-red-500/80 bg-red-700/25',
};

const ROW_HIGHLIGHT: Record<string, string> = {
  info: 'hover:bg-slate-900/70',
  warning: 'hover:bg-amber-950/20',
  error: 'bg-red-950/10 hover:bg-red-950/30',
  fatal: 'bg-red-950/30 hover:bg-red-950/50',
};

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour12: false });
}

export default function LogList({ logs, loading }: Props) {
  if (loading) {
    return (
      <section
        aria-label="System Log Stream"
        className="rounded-2xl border border-slate-700/80 bg-slate-950/85 p-4"
      >
        <div className="space-y-2" role="status" aria-live="polite">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="h-10 w-full animate-pulse rounded-md border border-slate-800 bg-slate-900/70"
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section aria-label="System Log Stream" className="rounded-2xl border border-slate-700/80 bg-slate-950/85">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2">
        <p className="text-[11px] font-mono uppercase tracking-[0.18em] text-slate-400">Timestamp / Node / Severity</p>
        <p className="text-[11px] font-mono text-slate-500">Live Poll: 5s</p>
      </div>

      {logs.length === 0 ? (
        <div className="px-4 py-14 text-center" role="status" aria-live="polite">
          <p className="font-mono text-sm text-slate-300">No log entries</p>
          <p className="mt-1 text-xs text-slate-500">Awaiting activity from execution services.</p>
        </div>
      ) : (
        <ScrollArea className="h-[62vh]">
          <ul className="divide-y divide-slate-800/80">
            {logs.map(log => (
              <li
                key={log.id}
                className={cn(
                  'grid grid-cols-[86px_92px_92px_1fr] items-start gap-2 px-4 py-2 font-mono text-xs leading-relaxed transition-colors',
                  ROW_HIGHLIGHT[log.severity] ?? ROW_HIGHLIGHT.info,
                )}
              >
                <span className="text-slate-500">{formatTime(log.created_at)}</span>
                <span className="truncate rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-cyan-100">
                  {log.node_id}
                </span>
                <span
                  className={cn(
                    'inline-flex justify-center rounded border px-2 py-0.5 uppercase tracking-[0.08em]',
                    SEVERITY_TONE[log.severity] ?? SEVERITY_TONE.info,
                  )}
                >
                  {log.severity}
                </span>
                <span
                  className={cn(
                    'break-words text-slate-200',
                    log.severity === 'fatal' && 'font-semibold text-red-100',
                    log.severity === 'error' && 'text-red-200',
                  )}
                >
                  {log.message}
                </span>
              </li>
            ))}
          </ul>
        </ScrollArea>
      )}
    </section>
  );
}

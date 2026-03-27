import { cn } from '@/lib/utils';
import type { PipelineStatus } from '@/types/api';

const STAGES: { id: PipelineStatus; label: string; icon: string; short: string }[] = [
  { id: 'idle', label: 'Idle', icon: 'hourglass_empty', short: 'I' },
  { id: 'scanning', label: 'Scanning', icon: 'radar', short: 'S' },
  { id: 'solving', label: 'Solving', icon: 'neurology', short: 'So' },
  { id: 'executing', label: 'Executing', icon: 'precision_manufacturing', short: 'E' },
  { id: 'done', label: 'Done', icon: 'task_alt', short: 'D' },
];

const STATUS_ORDER: Record<PipelineStatus, number> = {
  idle: 0,
  scanning: 1,
  solving: 2,
  executing: 3,
  done: 4,
  error: 4,
};

function getStageTone({ isComplete, isActive, isErrorStage }: { isComplete: boolean; isActive: boolean; isErrorStage: boolean }) {
  if (isErrorStage) {
    return {
      chip: 'border-red-500/40 bg-red-500/20 text-red-200 shadow-[0_0_0_1px_rgba(239,68,68,0.2)]',
      label: 'text-red-300',
      track: 'bg-red-500/60',
    };
  }
  if (isComplete) {
    return {
      chip: 'border-emerald-500/40 bg-emerald-500/20 text-emerald-100 shadow-[0_0_0_1px_rgba(16,185,129,0.2)]',
      label: 'text-emerald-300',
      track: 'bg-emerald-500/70',
    };
  }
  if (isActive) {
    return {
      chip: 'border-kl-primary/60 bg-kl-primary/20 text-kl-primary shadow-[0_0_20px_rgba(0,229,255,0.22)]',
      label: 'text-kl-primary',
      track: 'bg-kl-primary/70',
    };
  }
  return {
    chip: 'border-kl-outline-variant bg-kl-surface-low/70 text-kl-on-surface-variant',
    label: 'text-kl-on-surface-variant',
    track: 'bg-kl-outline-variant',
  };
}

export default function PipelineStepper({ status }: { status: PipelineStatus }) {
  const currentIdx = STATUS_ORDER[status] ?? 0;
  const isError = status === 'error';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.18em] text-kl-on-surface-variant">Pipeline State</p>
        <span
          className={cn(
            'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide',
            status === 'error' && 'border-red-500/40 bg-red-500/20 text-red-300',
            status === 'done' && 'border-emerald-500/40 bg-emerald-500/20 text-emerald-300',
            !['error', 'done'].includes(status) && 'border-kl-primary/40 bg-kl-primary/20 text-kl-primary',
          )}
        >
          {status}
        </span>
      </div>

      <div className="grid gap-2 sm:grid-cols-5">
        {STAGES.map((stage, idx) => {
          const isActive = idx === currentIdx && !isError;
          const isComplete = idx < currentIdx && !isError;
          const isErrorStage = isError && idx === currentIdx;
          const tone = getStageTone({ isComplete, isActive, isErrorStage });

          return (
            <div key={stage.id} className="flex flex-col gap-2">
              <div
                className={cn(
                  'flex items-center gap-2 rounded-xl border px-3 py-2 backdrop-blur-sm transition-colors',
                  tone.chip,
                )}
              >
                <span className="material-symbols-outlined text-base leading-none">{stage.icon}</span>
                <span className="text-xs font-semibold uppercase tracking-wide">{stage.short}</span>
              </div>
              <span className={cn('text-[11px] font-medium uppercase tracking-wide', tone.label)}>{stage.label}</span>

              {idx < STAGES.length - 1 && (
                <div className="hidden h-[3px] rounded-full sm:block bg-kl-surface-high">
                  <div
                    className={cn('h-full rounded-full transition-all', tone.track)}
                    style={{ width: isComplete || isActive || isErrorStage ? '100%' : '0%' }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {isError && (
        <p className="flex items-center gap-2 text-xs font-medium text-red-300">
          <span className="material-symbols-outlined text-sm">error</span>
          Pipeline ended in error. Check Activity Terminal for failure context.
        </p>
      )}
    </div>
  );
}

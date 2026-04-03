/**
 * @file PipelineStepper.tsx
 * @description Dashboard component: PipelineStepper
 */

import { cn } from '@/lib/utils';
import type { PipelineStatus } from '@/types/api';

const STAGES: { id: PipelineStatus; label: string; icon: string; short: string }[] = [
  { id: 'idle', label: 'Idle', icon: 'hourglass_empty', short: 'ID' },
  { id: 'scanning', label: 'Scanning', icon: 'radar', short: 'SC' },
  { id: 'solving', label: 'Solving', icon: 'neurology', short: 'SO' },
  { id: 'executing', label: 'Executing', icon: 'precision_manufacturing', short: 'EX' },
  { id: 'done', label: 'Done', icon: 'task_alt', short: 'OK' },
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
      chip: 'border-red-500/45 bg-red-500/18 text-red-100 shadow-[0_0_0_1px_rgba(239,68,68,0.25)]',
      label: 'text-red-300',
      rail: 'bg-red-500/70',
      dot: 'bg-red-300',
    };
  }
  if (isComplete) {
    return {
      chip: 'border-emerald-500/45 bg-emerald-500/15 text-emerald-100 shadow-[0_0_0_1px_rgba(16,185,129,0.2)]',
      label: 'text-emerald-300',
      rail: 'bg-emerald-400/85',
      dot: 'bg-emerald-300',
    };
  }
  if (isActive) {
    return {
      chip: 'border-kl-primary/65 bg-kl-primary/15 text-kl-primary shadow-[0_0_22px_rgba(0,229,255,0.28)]',
      label: 'text-kl-primary',
      rail: 'bg-kl-primary',
      dot: 'bg-kl-primary',
    };
  }
  return {
    chip: 'border-kl-outline-variant/80 bg-kl-surface-low/70 text-kl-on-surface-variant',
    label: 'text-kl-on-surface-variant',
    rail: 'bg-kl-outline-variant/70',
    dot: 'bg-kl-outline-variant',
  };
}

export default function PipelineStepper({ status }: { status: PipelineStatus }) {
  const currentIdx = STATUS_ORDER[status] ?? 0;
  const isError = status === 'error';

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-kl-on-surface-variant">Pipeline State</p>
          <h3 className="mt-1 text-base font-semibold text-kl-on-surface">Active Session Progress</h3>
        </div>
        <span
          className={cn(
            'inline-flex items-center rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em]',
            status === 'error' && 'border-red-500/45 bg-red-500/18 text-red-300',
            status === 'done' && 'border-emerald-500/45 bg-emerald-500/18 text-emerald-300',
            !['error', 'done'].includes(status) && 'border-kl-primary/45 bg-kl-primary/18 text-kl-primary',
          )}
        >
          {status}
        </span>
      </div>

      <div className="relative grid gap-3 sm:grid-cols-5">
        <div className="pointer-events-none absolute left-0 right-0 top-[23px] hidden h-px bg-kl-outline-variant/55 sm:block" />
        {STAGES.map((stage, idx) => {
          const isActive = idx === currentIdx && !isError;
          const isComplete = idx < currentIdx && !isError;
          const isErrorStage = isError && idx === currentIdx;
          const reached = isComplete || isActive || isErrorStage;
          const tone = getStageTone({ isComplete, isActive, isErrorStage });

          return (
            <div key={stage.id} className="relative z-10 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className={cn('h-2.5 w-2.5 rounded-full shadow-[0_0_12px_rgba(0,0,0,0.35)]', reached ? tone.dot : 'bg-kl-outline-variant/70')} />
                <span className={cn('h-[2px] flex-1 rounded-full sm:hidden', reached ? tone.rail : 'bg-kl-outline-variant/70')} />
              </div>

              <div className={cn('flex items-center gap-2 rounded-xl border px-3 py-2.5 backdrop-blur-sm transition-colors', tone.chip)}>
                <span className="material-symbols-outlined text-base leading-none">{stage.icon}</span>
                <span className="text-[11px] font-semibold uppercase tracking-[0.14em]">{stage.short}</span>
              </div>

              <div className="space-y-1">
                <p className={cn('text-[11px] font-semibold uppercase tracking-[0.14em]', tone.label)}>{stage.label}</p>
                <div className="hidden h-1.5 rounded-full bg-kl-surface-high sm:block">
                  <div className={cn('h-full rounded-full transition-all duration-300', tone.rail)} style={{ width: reached ? '100%' : '0%' }} />
                </div>
              </div>
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

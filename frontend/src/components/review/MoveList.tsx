import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import type { SolutionStep } from '@/types/api';

interface Props {
  steps: SolutionStep[];
  currentStep: number;
}

export default function MoveList({ steps, currentStep }: Props) {
  if (steps.length === 0) {
    return (
      <p className="text-slate-500 text-sm">No moves recorded for this session.</p>
    );
  }

  return (
    <ScrollArea className="h-96 rounded-xl border border-kl-outline-variant/70 bg-kl-surface-low/45">
      <div className="space-y-1 p-3 sm:p-4">
        {steps.map((step, idx) => {
          const isActive = idx === currentStep;
          const isDone = idx < currentStep;
          return (
            <div
              key={step.step_index}
              className={cn(
                'flex min-h-10 items-center gap-3 rounded-md border px-3 py-2 font-mono text-xs sm:text-sm transition-colors',
                'border-transparent bg-kl-surface-low/30',
                isActive && 'border-cyan-400/35 bg-cyan-500/[0.08] text-cyan-100',
                isDone && 'bg-kl-surface-low/25 text-kl-outline',
                !isActive && !isDone && 'text-kl-on-surface-variant',
              )}
            >
              <span className="w-8 text-right tracking-wide text-kl-outline">{String(idx + 1).padStart(2, '0')}</span>
              <span className={cn('truncate tracking-wide', isActive && 'font-semibold text-cyan-100')}>
                {step.move_notation}
              </span>

              {isDone && <span className="ml-auto text-[11px] uppercase tracking-wide text-emerald-300">done</span>}
              {isActive && <span className="ml-auto text-[11px] uppercase tracking-wide text-cyan-300">active</span>}
              {!isDone && !isActive && <span className="ml-auto text-[11px] uppercase tracking-wide text-kl-outline">queued</span>}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

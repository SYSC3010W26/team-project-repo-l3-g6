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
    <ScrollArea className="h-96 rounded-lg border border-slate-800 bg-slate-900/50">
      <div className="p-4 space-y-1">
        {steps.map((step, idx) => {
          const isActive = idx === currentStep;
          const isDone = idx < currentStep;
          return (
            <div
              key={step.step_index}
              className={cn(
                'flex items-center gap-4 px-3 py-2 rounded-md transition-colors',
                isActive && 'bg-blue-600/20 border border-blue-500/30',
                isDone && 'opacity-50'
              )}
            >
              <span className="text-slate-500 text-xs w-6 text-right">{idx + 1}</span>
              <span className={cn(
                'font-mono text-sm',
                isActive ? 'text-blue-300 font-semibold' : 'text-slate-300',
                isDone && 'text-slate-500'
              )}>
                {step.move_notation}
              </span>
              {isDone && <span className="ml-auto text-green-500 text-xs">✓</span>}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

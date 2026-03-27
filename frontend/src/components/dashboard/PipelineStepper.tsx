import { cn } from '@/lib/utils';
import type { PipelineStatus } from '@/types/api';

const STAGES: { id: PipelineStatus; label: string }[] = [
  { id: 'idle', label: 'Idle' },
  { id: 'scanning', label: 'Scanning' },
  { id: 'solving', label: 'Solving' },
  { id: 'executing', label: 'Executing' },
  { id: 'done', label: 'Done' },
];

const STATUS_ORDER: Record<PipelineStatus, number> = {
  idle: 0, scanning: 1, solving: 2, executing: 3, done: 4, error: 4,
};

export default function PipelineStepper({ status }: { status: PipelineStatus }) {
  const currentIdx = STATUS_ORDER[status] ?? 0;
  const isError = status === 'error';

  return (
    <div className="flex items-center gap-0 flex-wrap">
      {STAGES.map((stage, idx) => {
        const isActive = idx === currentIdx && !isError;
        const isComplete = idx < currentIdx && !isError;
        const isErrorStage = isError && idx === currentIdx;
        return (
          <div key={stage.id} className="flex items-center">
            <div className="flex flex-col items-center gap-1">
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
                isComplete && 'bg-green-500 text-white',
                isActive && 'bg-blue-500 text-white ring-2 ring-blue-500/30',
                isErrorStage && 'bg-red-500 text-white',
                !isActive && !isComplete && !isErrorStage && 'bg-slate-800 text-slate-500',
              )}>
                {isComplete ? '✓' : idx + 1}
              </div>
              <span className={cn(
                'text-xs',
                isActive && 'text-blue-400 font-medium',
                isErrorStage && 'text-red-400 font-medium',
                isComplete && 'text-green-400',
                !isActive && !isComplete && !isErrorStage && 'text-slate-500',
              )}>{stage.label}</span>
            </div>
            {idx < STAGES.length - 1 && (
              <div className={cn(
                'h-px w-8 mx-1 mt-[-12px]',
                idx < currentIdx && !isError ? 'bg-green-500' : 'bg-slate-700'
              )} />
            )}
          </div>
        );
      })}
      {isError && (
        <div className="ml-4 text-red-400 text-sm font-medium">⚠ Error</div>
      )}
    </div>
  );
}

import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Move {
  index: number;
  notation: string;
}

interface Props {
  moves: Move[];
  currentStep: number;
}

export default function MoveProgressList({ moves, currentStep }: Props) {
  if (moves.length === 0) return null;

  return (
    <ScrollArea className="h-80 rounded-xl border border-kl-outline-variant/70 bg-kl-surface-low/45">
      <div className="space-y-1 p-3 sm:p-4">
        {moves.map((move) => {
          const isActive = move.index === currentStep;
          const isDone = move.index < currentStep;

          return (
            <div
              key={move.index}
              className={cn(
                'flex min-h-10 items-center gap-3 rounded-md border px-3 py-2 font-mono text-xs sm:text-sm transition-colors',
                'border-transparent bg-kl-surface-low/30',
                isActive && 'border-cyan-400/35 bg-cyan-500/[0.08] text-cyan-100',
                isDone && 'bg-kl-surface-low/25 text-kl-outline',
                !isActive && !isDone && 'text-kl-on-surface-variant',
              )}
            >
              <span className="w-8 text-right tracking-wide text-kl-outline">{String(move.index + 1).padStart(2, '0')}</span>
              <span className={cn('truncate tracking-wide', isActive && 'font-semibold text-cyan-100')}>
                {move.notation}
              </span>

              {isDone && <span className="ml-auto text-[11px] uppercase tracking-wide text-emerald-300">done</span>}
              {isActive && <span className="ml-auto animate-pulse text-[11px] uppercase tracking-wide text-cyan-300">live</span>}
              {!isDone && !isActive && <span className="ml-auto text-[11px] uppercase tracking-wide text-kl-outline">queued</span>}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

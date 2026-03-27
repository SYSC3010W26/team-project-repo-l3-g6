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
    <ScrollArea className="h-80 rounded-lg border border-slate-800 bg-slate-900/50">
      <div className="p-3 space-y-0.5">
        {moves.map(move => {
          const isActive = move.index === currentStep;
          const isDone = move.index < currentStep;
          return (
            <div
              key={move.index}
              className={cn(
                'flex items-center gap-4 px-3 py-1.5 rounded-md',
                isActive && 'bg-blue-600/20 border border-blue-500/20',
              )}
            >
              <span className="text-slate-600 text-xs w-5 text-right">{move.index + 1}</span>
              <span className={cn(
                'font-mono text-sm',
                isActive ? 'text-blue-300 font-semibold' : '',
                isDone ? 'text-slate-600' : 'text-slate-300',
              )}>
                {move.notation}
              </span>
              {isDone && <span className="ml-auto text-green-500 text-xs">✓</span>}
              {isActive && <span className="ml-auto text-blue-400 text-xs animate-pulse">▶</span>}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

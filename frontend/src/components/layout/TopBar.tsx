import { useSocketStatus } from '@/hooks/useSocket';
import { cn } from '@/lib/utils';

export default function TopBar() {
  const connected = useSocketStatus();
  return (
    <header className="h-14 border-b border-slate-800 bg-slate-900/50 backdrop-blur flex items-center justify-between px-4 md:px-6 sticky top-0 z-10">
      <span className="md:hidden font-bold text-white">Pi³ Solver</span>
      <div className="flex-1" />
      <div className="flex items-center gap-2">
        <span
          className={cn(
            'w-2 h-2 rounded-full',
            connected ? 'bg-green-500 animate-pulse' : 'bg-amber-500'
          )}
        />
        <span className="text-xs text-slate-400">
          {connected ? 'Live' : 'Disconnected'}
        </span>
      </div>
    </header>
  );
}

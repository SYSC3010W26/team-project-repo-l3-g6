import { useSocketStatus } from '@/hooks/useSocket';
import { cn } from '@/lib/utils';

export default function TopBar() {
  const connected = useSocketStatus();

  return (
    <header className="fixed top-0 w-full z-50 glass flex justify-between items-center px-8 py-4">
      {/* Brand */}
      <div className="text-2xl font-bold tracking-tighter text-kl-primary uppercase font-headline">
        RUBIK'S SOLVER
      </div>

      {/* Center Nav — hidden on mobile */}
      <nav className="hidden md:flex space-x-8">
        <span className="text-kl-on-surface-variant font-headline tracking-tight text-sm">
          Pi³ Autonomous Platform
        </span>
      </nav>

      {/* Right — icons + connection status */}
      <div className="flex items-center gap-3">
        <button className="text-kl-on-surface-variant hover:bg-kl-surface-high p-2 rounded-full transition-all active:scale-95">
          <span className="material-symbols-outlined text-[20px]">history</span>
        </button>
        <button className="text-kl-on-surface-variant hover:bg-kl-surface-high p-2 rounded-full transition-all active:scale-95">
          <span className="material-symbols-outlined text-[20px]">settings</span>
        </button>

        {/* Connection indicator */}
        <div className="flex items-center gap-2 ml-2 pl-3 border-l border-kl-outline-variant/30">
          <span
            className={cn(
              'w-2 h-2 rounded-full',
              connected ? 'bg-kl-tertiary animate-pulse' : 'bg-kl-error'
            )}
          />
          <span className={cn(
            'text-[10px] uppercase tracking-widest font-headline',
            connected ? 'text-kl-tertiary' : 'text-kl-error'
          )}>
            {connected ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}

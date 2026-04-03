import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { PipelineStatus } from '@/types/api';

interface Props {
  status: PipelineStatus;
  sessionId: number | string | null;
  onAction: (action: string) => void;
  loading?: boolean;
}

function controlButtonClass({
  intent,
  disabled,
}: {
  intent: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
}) {
  if (disabled) return '';

  if (intent === 'primary') {
    return 'border border-kl-primary/40 bg-kl-primary text-black shadow-[0_0_24px_rgba(0,229,255,0.32)] hover:bg-kl-primary/90';
  }

  if (intent === 'danger') {
    return 'border border-red-500/45 bg-red-500/18 text-red-200 shadow-[0_0_14px_rgba(239,68,68,0.18)] hover:bg-red-500/25';
  }

  return 'border-kl-outline-variant bg-kl-surface-low/50 text-kl-on-surface hover:bg-kl-surface-high';
}

export default function ControlButtons({ status, onAction, loading }: Props) {
  const isIdle = status === 'idle';
  const isActive = ['scanning', 'solving', 'executing'].includes(status);
  const isDone = ['done', 'error'].includes(status);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Button
          onClick={() => onAction('start')}
          disabled={!isIdle || loading}
          className={cn(
            'h-11 justify-start gap-2 font-medium',
            controlButtonClass({ intent: 'primary', disabled: !isIdle || loading }),
          )}
        >
          <span className="material-symbols-outlined text-base">play_arrow</span>
          Start Solve
        </Button>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              disabled={!isActive || loading}
              className={cn(
                'h-11 justify-start gap-2 font-medium',
                controlButtonClass({ intent: 'danger', disabled: !isActive || loading }),
              )}
            >
              <span className="material-symbols-outlined text-base">stop_circle</span>
              Stop
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Stop Solve</AlertDialogTitle>
              <AlertDialogDescription>
                This will halt the current solve sequence.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => onAction('stop')} className="bg-red-600 hover:bg-red-700">
                Stop
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              disabled={!isDone || loading}
              className={cn(
                'h-11 justify-start gap-2 font-medium',
                controlButtonClass({ intent: 'secondary', disabled: !isDone || loading }),
              )}
            >
              <span className="material-symbols-outlined text-base">restart_alt</span>
              Reset
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Reset Session</AlertDialogTitle>
              <AlertDialogDescription>
                This will clear the current session and return to Idle.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => onAction('reset')}>Reset</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <Button
          variant="outline"
          onClick={() => onAction('rescan')}
          disabled={!isDone || loading}
          className={cn(
            'h-11 justify-start gap-2 font-medium',
            controlButtonClass({ intent: 'secondary', disabled: !isDone || loading }),
          )}
        >
          <span className="material-symbols-outlined text-base">refresh</span>
          Rescan
        </Button>
      </div>

      <p className="text-[11px] uppercase tracking-[0.16em] text-kl-on-surface-variant">
        Controls remain state-gated by live pipeline status.
      </p>
    </div>
  );
}

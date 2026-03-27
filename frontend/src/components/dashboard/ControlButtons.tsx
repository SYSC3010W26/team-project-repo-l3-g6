import { Button } from '@/components/ui/button';
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
import type { PipelineStatus } from '@/types/api';

interface Props {
  status: PipelineStatus;
  sessionId: string | null;
  onAction: (action: string) => void;
  loading?: boolean;
}

export default function ControlButtons({ status, sessionId: _sessionId, onAction, loading }: Props) {
  const isIdle = status === 'idle';
  const isActive = ['scanning', 'solving', 'executing'].includes(status);
  const isDone = ['done', 'error'].includes(status);

  return (
    <div className="flex flex-wrap gap-3">
      <Button
        onClick={() => onAction('start')}
        disabled={!isIdle || loading}
        className="bg-blue-600 hover:bg-blue-700 text-white"
      >
        Start Solve
      </Button>

      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="destructive" disabled={!isActive || loading}>Stop</Button>
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
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
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
        className="border-slate-700 text-slate-300 hover:bg-slate-800"
      >
        Rescan
      </Button>
    </div>
  );
}

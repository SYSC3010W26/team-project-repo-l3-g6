import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import type { ExecutionProgressUpdate } from '@/types/api';

interface Props {
  progress: ExecutionProgressUpdate | null;
}

export default function ProgressHeader({ progress }: Props) {
  if (!progress) return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-slate-400 text-sm">No active execution</span>
        <Badge className="bg-slate-700 text-slate-400">0 / 0</Badge>
      </div>
      <Progress value={0} className="h-2 bg-slate-800" />
    </div>
  );

  const pct = Math.round(progress.pct_complete * 100);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-white font-mono text-lg font-semibold">{progress.move}</span>
          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">Executing</Badge>
        </div>
        <Badge className="bg-slate-700 text-slate-200">
          {progress.current_step} / {progress.total_steps}
        </Badge>
      </div>
      <Progress value={pct} className="h-3 bg-slate-800" />
      <p className="text-slate-400 text-xs text-right">{pct}% complete</p>
    </div>
  );
}

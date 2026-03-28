import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import type { ExecutionProgressUpdate } from '@/types/api';

interface Props {
  progress: ExecutionProgressUpdate | null;
}

export default function ProgressHeader({ progress }: Props) {
  if (!progress) {
    return (
      <div className="space-y-4 rounded-xl border border-kl-outline-variant/70 bg-kl-surface-low/50 p-4">
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-kl-on-surface-variant">No active execution</span>
          <Badge className="border border-kl-outline-variant bg-kl-surface text-kl-on-surface-variant">0 / 0</Badge>
        </div>
        <Progress value={0} className="h-2 bg-kl-surface-high" />
        <p className="text-right text-xs text-kl-outline">Waiting for execution progress…</p>
      </div>
    );
  }

  const pct = Math.round(progress.pct_complete * 100);

  return (
    <div className="space-y-4 rounded-xl border border-cyan-400/30 bg-cyan-500/[0.06] p-4 shadow-[0_0_40px_rgba(80,225,249,0.08)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-lg font-semibold tracking-wide text-kl-on-surface">{progress.move}</span>
          <Badge className="border border-cyan-400/35 bg-cyan-400/10 text-cyan-200">Executing</Badge>
        </div>
        <Badge className="border border-kl-primary/40 bg-kl-primary/10 font-mono text-kl-primary">
          {progress.current_step} / {progress.total_steps}
        </Badge>
      </div>

      <Progress value={pct} className="h-3 bg-kl-surface-high" />

      <div className="flex items-center justify-between text-xs">
        <span className="font-mono text-cyan-200">live progress</span>
        <span className="font-mono text-cyan-300">{pct}% complete</span>
      </div>
    </div>
  );
}

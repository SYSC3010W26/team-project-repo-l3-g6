import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { SystemLog } from '@/types/api';

interface Props {
  logs: SystemLog[];
  loading: boolean;
}

const SEVERITY_STYLES: Record<string, string> = {
  info: 'bg-slate-700 text-slate-300',
  warning: 'bg-amber-500/20 text-amber-400',
  error: 'bg-red-500/20 text-red-400',
  fatal: 'bg-red-600/20 text-red-300 border-red-500/40',
};

export default function LogList({ logs, loading }: Props) {
  if (loading) return (
    <div className="space-y-2">
      {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-10 w-full rounded" />)}
    </div>
  );

  if (logs.length === 0) return (
    <div className="text-center py-16">
      <p className="text-slate-400 font-medium">No log entries</p>
      <p className="text-slate-500 text-sm mt-1">Events will appear here once a solve runs.</p>
    </div>
  );

  return (
    <ScrollArea className="h-[60vh] rounded-lg border border-slate-800">
      <div className="divide-y divide-slate-800">
        {logs.map(log => (
          <div
            key={log.id}
            className={cn(
              'flex items-start gap-3 px-4 py-2.5',
              log.severity === 'fatal' && 'bg-red-950/30',
            )}
          >
            <span className="text-slate-600 text-xs font-mono whitespace-nowrap mt-0.5 w-20">
              {new Date(log.created_at).toLocaleTimeString()}
            </span>
            <Badge className="text-xs shrink-0 capitalize"
              style={{ backgroundColor: 'transparent' }}
              variant="outline">
              {log.node_id}
            </Badge>
            <Badge className={cn('text-xs shrink-0 capitalize', SEVERITY_STYLES[log.severity])}>
              {log.severity}
            </Badge>
            <span className={cn(
              'text-sm leading-snug',
              log.severity === 'fatal' ? 'text-red-300' : 'text-slate-300',
              log.severity === 'error' && 'text-red-400',
            )}>
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}

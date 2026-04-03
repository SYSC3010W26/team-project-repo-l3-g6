/**
 * @file SeverityFilter.tsx
 * @description Logs component: SeverityFilter
 */

import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

type Severity = 'all' | 'info' | 'warning' | 'error' | 'fatal';

interface Props {
  severity: Severity;
  onSeverityChange: (s: Severity) => void;
  node: string;
  onNodeChange: (n: string) => void;
}

const SEVERITIES: { value: Severity; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'error', label: 'Error' },
  { value: 'fatal', label: 'Fatal' },
];

const NODES = ['all', 'scanner', 'solver', 'motor', 'database'];

const ACTIVE_STYLES: Record<Severity, string> = {
  all: 'data-[state=on]:border-cyan-400/60 data-[state=on]:bg-cyan-500/20 data-[state=on]:text-cyan-100',
  info: 'data-[state=on]:border-slate-400/60 data-[state=on]:bg-slate-500/20 data-[state=on]:text-slate-100',
  warning: 'data-[state=on]:border-amber-400/70 data-[state=on]:bg-amber-500/20 data-[state=on]:text-amber-100',
  error: 'data-[state=on]:border-red-400/70 data-[state=on]:bg-red-500/20 data-[state=on]:text-red-100',
  fatal: 'data-[state=on]:border-red-500/80 data-[state=on]:bg-red-600/25 data-[state=on]:text-red-50',
};

export default function SeverityFilter({ severity, onSeverityChange, node, onNodeChange }: Props) {
  return (
    <section className="rounded-2xl border border-slate-700/70 bg-slate-900/55 p-4 backdrop-blur-md" aria-label="Log Filters">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-2">
          <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-slate-400">Severity</p>
          <ToggleGroup
            type="single"
            value={severity}
            onValueChange={v => onSeverityChange((v as Severity) || 'all')}
            className="flex-wrap justify-start gap-2"
            aria-label="Severity Filter"
          >
            {SEVERITIES.map(s => (
              <ToggleGroupItem
                key={s.value}
                value={s.value}
                className={cn(
                  'h-8 rounded-md border border-slate-700 bg-slate-950/70 px-3 text-[11px] font-mono uppercase tracking-[0.08em] text-slate-300 transition-colors',
                  ACTIVE_STYLES[s.value],
                )}
              >
                {s.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>

        <div className="space-y-2">
          <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-slate-400">Node</p>
          <Select value={node} onValueChange={onNodeChange}>
            <SelectTrigger className="h-8 w-44 rounded-md border-slate-700 bg-slate-950/80 text-xs font-mono text-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="border-slate-700 bg-slate-900 text-slate-100">
              {NODES.map(n => (
                <SelectItem key={n} value={n} className="text-xs font-mono capitalize text-slate-200">
                  {n === 'all' ? 'All Nodes' : n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </section>
  );
}

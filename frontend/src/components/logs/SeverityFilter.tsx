import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

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

export default function SeverityFilter({ severity, onSeverityChange, node, onNodeChange }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <ToggleGroup
        type="single"
        value={severity}
        onValueChange={v => onSeverityChange((v as Severity) || 'all')}
        className="flex-wrap"
      >
        {SEVERITIES.map(s => (
          <ToggleGroupItem key={s.value} value={s.value}
            className="text-xs data-[state=on]:bg-blue-600/20 data-[state=on]:text-blue-400">
            {s.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      <Select value={node} onValueChange={onNodeChange}>
        <SelectTrigger className="w-36 bg-slate-900 border-slate-700 text-slate-300 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="bg-slate-900 border-slate-700">
          {NODES.map(n => (
            <SelectItem key={n} value={n} className="text-slate-300 text-xs">{n === 'all' ? 'All Nodes' : n}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

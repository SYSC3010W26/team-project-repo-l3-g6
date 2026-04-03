/**
 * @file SessionTable.tsx
 * @description Results component: SessionTable
 */

import { useNavigate } from 'react-router-dom';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { SolveSession } from '@/types/api';

interface Props {
  sessions: SolveSession[];
  loading: boolean;
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    done: 'bg-green-500/20 text-green-400 border-green-500/30',
    error: 'bg-red-500/20 text-red-400 border-red-500/30',
    executing: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };
  return (
    <Badge className={colorMap[status] ?? 'bg-slate-500/20 text-slate-400 border-slate-500/30'}>
      {status}
    </Badge>
  );
}

export default function SessionTable({ sessions, loading }: Props) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-12 w-full rounded" />)}
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400 text-lg font-medium">No solve sessions yet</p>
        <p className="text-slate-500 text-sm mt-2">Start a solve to see results here.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-800 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-slate-800 hover:bg-transparent">
            <TableHead className="text-slate-400">Session</TableHead>
            <TableHead className="text-slate-400">Name</TableHead>
            <TableHead className="text-slate-400">Algorithm</TableHead>
            <TableHead className="text-slate-400">Completed</TableHead>
            <TableHead className="text-slate-400">Status</TableHead>
            <TableHead className="text-slate-400">Started</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.map((session) => (
            <TableRow
              key={session.session_id}
              className="border-slate-800 cursor-pointer hover:bg-slate-800/50"
              onClick={() => navigate(`/review/${session.session_id}`)}
            >
              <TableCell className="font-mono text-xs text-slate-300">
                #{session.session_id}
              </TableCell>
              <TableCell className="text-slate-300">
                {session.session_name ?? '—'}
              </TableCell>
              <TableCell className="text-slate-300">
                {session.selected_algorithm ?? '—'}
              </TableCell>
              <TableCell className="text-slate-300">
                {session.completed_at ? 'Yes' : '—'}
              </TableCell>
              <TableCell><StatusBadge status={session.status} /></TableCell>
              <TableCell className="text-slate-500 text-xs">
                {new Date(session.started_at).toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

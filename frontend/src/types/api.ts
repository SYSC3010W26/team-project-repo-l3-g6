/**
 * @file api.ts
 * @description Type or Hook: api
 */

export type PipelineStatus = 'idle' | 'scanning' | 'solving' | 'executing' | 'done' | 'error';

export interface JobState {
  session_id: number;
  status: PipelineStatus;
  created_at: string;
}

export interface NodeStatus {
  node_id: string;
  node_type: string;
  is_online: boolean;
  last_heartbeat: string | null;
}

export interface JobStateUpdate {
  session_id: number;
  status: PipelineStatus;
  node_status: Record<string, boolean>;
}

export interface ExecutionProgressUpdate {
  session_id: number;
  current_step: number;
  total_steps: number;
  move: string;
  pct_complete: number;
}

export interface SolveSession {
  session_id: number;
  status: PipelineStatus;
  selected_algorithm: string;
  session_name: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface SolutionStep {
  step_index: number;
  move_notation: string;
}

export interface SystemLog {
  id: number;
  session_id: number | null;
  node_id: string | null;
  severity: 'info' | 'warning' | 'error' | 'fatal' | string;
  event_type: string;
  message: string;
  metadata: string | null;
  created_at: string;
}

export interface CubeState {
  session_id: number;
  state_string: string;
  is_valid: boolean;
  confidence: number | null;
  created_at: string;
}

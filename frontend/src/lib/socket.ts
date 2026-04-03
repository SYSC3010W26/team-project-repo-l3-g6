/**
 * @file socket.ts
 * @description Configures and exports the Socket.IO client instance for real-time communication.
 */

import { io, type Socket } from 'socket.io-client';
import type { JobStateUpdate, ExecutionProgressUpdate } from '@/types/api';

export interface ServerToClientEvents {
  job_state_update: (data: JobStateUpdate) => void;
  execution_progress: (data: ExecutionProgressUpdate) => void;
}

const socket: Socket<ServerToClientEvents> = io('/', {
  path: '/socket.io',
  transports: ['websocket'],
  autoConnect: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 2000,
});

export default socket;

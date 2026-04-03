/**
 * @file api.ts
 * @description Axios-based API client and service functions for backend communication.
 */

import axios from 'axios';
import type {
  JobState,
  NodeStatus,
  SolveSession,
  SystemLog,
  CubeState,
} from '@/types/api';

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const getJobState = (sessionId: string | number): Promise<JobState> =>
  api.get(`/jobs/${sessionId}`).then((r) => r.data);

export const getAllNodes = (): Promise<NodeStatus[]> =>
  api.get('/nodes/status').then((r) => r.data);

export const getSessions = (): Promise<SolveSession[]> =>
  api.get('/jobs').then((r) => r.data);

export const getSolution = (sessionId: string | number) =>
  api.get(`/solve/${sessionId}`).then((r) => r.data);

export const getLogs = (severity?: string, node?: string): Promise<SystemLog[]> =>
  api.get('/logs', { params: { severity, node } }).then((r) => r.data);

export const postControlFlag = (sessionId: string | number, action: string) =>
  api.post(`/jobs/${sessionId}/control`, { action, issued_by: 'gui' });

export const startSolve = () =>
  api.post('/jobs/start').then((r) => r.data);

export const getScanState = (sessionId: string | number): Promise<CubeState> =>
  api.get('/scan/' + sessionId).then((r) => r.data);

import axios from 'axios';

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const getJobState = (sessionId: string) =>
  api.get(`/jobs/${sessionId}`).then((r) => r.data);

export const getAllNodes = () =>
  api.get('/nodes/status').then((r) => r.data);

export const getSessions = () =>
  api.get('/jobs').then((r) => r.data);

export const getSolution = (sessionId: string) =>
  api.get(`/solve/${sessionId}`).then((r) => r.data);

export const getLogs = (severity?: string, node?: string) =>
  api.get('/logs', { params: { severity, node } }).then((r) => r.data);

export const postControlFlag = (sessionId: string, action: string) =>
  api.post(`/jobs/${sessionId}/control`, { action, issued_by: 'gui' });

export const startSolve = () =>
  api.post('/jobs/start').then((r) => r.data);

export const getScanState = (sessionId: string) =>
  api.get('/scan/' + sessionId).then((r) => r.data);

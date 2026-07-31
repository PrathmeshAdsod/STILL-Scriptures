import { clientConfig } from './config';
import { activeFirebaseUid, getIdToken } from './firebase';
import type { AccountStatus, Echo, Project, ViewingSession } from '../types';

type ApiErrorPayload = { detail?: { message?: string } | string };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  const token = await getIdToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (clientConfig.appMode !== 'production') headers.set('X-Development-User', activeFirebaseUid() ?? 'local-user');
  const response = await fetch(`${clientConfig.apiBaseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    const detail = typeof body.detail === 'string' ? body.detail : body.detail?.message;
    throw new Error(detail ?? `Request failed (${response.status}).`);
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}

export const api = {
  getAccount: () => request<AccountStatus>('/account'),
  redeemAccessCode: (code: string) => request<AccountStatus>('/account/access-code', { method: 'POST', body: JSON.stringify({ code }) }),
  createProject: (title: string) => request<{ project_id: string }>('/projects', { method: 'POST', body: JSON.stringify({ title }) }),
  setYoutubeSource: (projectId: string, url: string, title?: string, duration_seconds?: number) => request<Project>(`/projects/${projectId}/source/youtube`, { method: 'POST', body: JSON.stringify({ url, title, duration_seconds }) }),
  completeUpload: (projectId: string, payload: object) => request<Project>(`/projects/${projectId}/source/upload-complete`, { method: 'POST', body: JSON.stringify(payload) }),
  startAnalysis: (projectId: string) => request<{ job_id: string }>(`/projects/${projectId}/analysis`, { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() } }),
  getProject: (projectId: string) => request<{ project: Project }>(`/projects/${projectId}`),
  getStatus: (projectId: string) => request<Project>(`/projects/${projectId}/status`),
  createSession: (projectId: string) => request<{ session_id: string }>(`/projects/${projectId}/viewing-sessions`, { method: 'POST' }),
  updateSession: (projectId: string, sessionId: string, payload: { ranges: Array<[number, number]>; duration_seconds: number; ended_naturally: boolean }) => request<ViewingSession>(`/projects/${projectId}/viewing-sessions/${sessionId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  getEchoes: (projectId: string, sessionId: string) => request<Echo[]>(`/projects/${projectId}/echoes?session_id=${encodeURIComponent(sessionId)}`),
  getStoryReflection: (projectId: string, sessionId: string) => request<Echo[]>(`/projects/${projectId}/story-reflection?session_id=${encodeURIComponent(sessionId)}`, { method: 'POST' }),
};

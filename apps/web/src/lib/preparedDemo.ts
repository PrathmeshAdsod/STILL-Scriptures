import { doc, getDoc } from 'firebase/firestore';
import { firebaseDb, signInJudgeAnonymously } from './firebase';
import type { Echo, PreparedDemo } from '../types';

export function normalizeDemoCode(value: string): string {
  return value.trim().toUpperCase();
}

export async function demoDocumentId(value: string): Promise<string> {
  const normalized = normalizeDemoCode(value);
  if (!normalized) throw new Error('Enter the judge demo code.');
  const bytes = new TextEncoder().encode(normalized);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function parsePreparedDemo(value: unknown): PreparedDemo {
  if (!isRecord(value) || value.schema_version !== 1 || !isRecord(value.project) || !Array.isArray(value.echoes) || !isRecord(value.provenance)) {
    throw new Error('The prepared demo record is invalid.');
  }
  const project = value.project;
  const source = project.source;
  const provenance = value.provenance;
  if (typeof project.id !== 'string' || typeof project.title !== 'string' || !isRecord(source) || source.kind !== 'youtube' || source.prepared_demo !== true || typeof source.public_url !== 'string' || typeof source.duration_seconds !== 'number') {
    throw new Error('The prepared demo source is invalid.');
  }
  if (provenance.outcome !== 'ACCEPTED_ECHO' || typeof provenance.source_url !== 'string' || provenance.source_url !== source.public_url || value.echoes.length === 0) {
    throw new Error('This demo does not contain an accepted, source-matched Echo.');
  }
  return value as unknown as PreparedDemo;
}

export function visibleDemoEchoes(echoes: Echo[], frontierSeconds: number): Echo[] {
  return echoes.filter((echo) => echo.knowledge_cutoff_seconds <= frontierSeconds);
}

export async function loadPreparedDemo(code: string): Promise<PreparedDemo> {
  if (!firebaseDb) throw new Error('The public Firebase demo is not configured.');
  await signInJudgeAnonymously();
  const snapshot = await getDoc(doc(firebaseDb, 'prepared_demos', await demoDocumentId(code)));
  if (!snapshot.exists()) throw new Error('That judge demo code was not recognised.');
  return parsePreparedDemo(snapshot.data());
}

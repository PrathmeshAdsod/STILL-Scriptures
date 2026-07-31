import { describe, expect, it } from 'vitest';
import { demoDocumentId, normalizeDemoCode, parsePreparedDemo, visibleDemoEchoes } from './preparedDemo';
import type { Echo, PreparedDemo } from '../types';

const echo: Echo = {
  id: 'echo-1', project_id: 'demo-1', knowledge_cutoff_seconds: 42,
  first_view_interpretation: 'A first-view reading', tension: 'A real tension',
  scene_context: 'A grounded scene', confidence: 0.9,
};

const demo: PreparedDemo = {
  schema_version: 1,
  judge_label: 'Prepared judge demo',
  project: {
    id: 'demo-1', title: 'A story', status: 'READY',
    source: { kind: 'youtube', public_url: 'https://youtu.be/example', title: 'A story', duration_seconds: 60, prepared_demo: true },
    progress: { completed_windows: 2, total_windows: 2, stage: 'ready' },
  },
  echoes: [echo],
  provenance: {
    generated_at: '2026-08-01T00:00:00Z', source_url: 'https://youtu.be/example',
    source_rights_note: 'Verified for demo use', analysis_windows: 2,
    pipeline: ['Gemini', 'Gloo', 'YouVersion'], outcome: 'ACCEPTED_ECHO',
  },
};

describe('prepared demo boundary', () => {
  it('normalises equivalent judge codes to one opaque document id', async () => {
    expect(normalizeDemoCode(' still-judge ')).toBe('STILL-JUDGE');
    expect(await demoDocumentId(' still-judge ')).toBe(await demoDocumentId('STILL-JUDGE'));
  });

  it('rejects records without a real accepted source-matched echo', () => {
    expect(parsePreparedDemo(demo)).toEqual(demo);
    expect(() => parsePreparedDemo({ ...demo, echoes: [] })).toThrow(/accepted/i);
    expect(() => parsePreparedDemo({ ...demo, provenance: { ...demo.provenance, source_url: 'https://youtu.be/other' } })).toThrow(/source-matched/i);
  });

  it('keeps future echoes behind the watched frontier', () => {
    expect(visibleDemoEchoes([echo], 41.9)).toEqual([]);
    expect(visibleDemoEchoes([echo], 42)).toEqual([echo]);
  });
});

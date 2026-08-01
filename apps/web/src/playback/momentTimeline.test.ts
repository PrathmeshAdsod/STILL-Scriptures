import { describe, expect, it } from 'vitest';
import { timelinePercent } from './momentTimeline';

describe('timelinePercent', () => {
  it('maps a playback timestamp onto the video timeline', () => {
    expect(timelinePercent(90, 180)).toBe(50);
  });

  it('clamps positions to the visible rail', () => {
    expect(timelinePercent(-20, 180)).toBe(0);
    expect(timelinePercent(200, 180)).toBe(100);
  });

  it('stays at the start when duration is unavailable', () => {
    expect(timelinePercent(20, 0)).toBe(0);
  });
});

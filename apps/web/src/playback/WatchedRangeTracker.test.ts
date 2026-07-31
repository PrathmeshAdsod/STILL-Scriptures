import { describe, expect, it } from 'vitest';
import { WatchedRangeTracker, contiguousFrontier } from './WatchedRangeTracker';

describe('WatchedRangeTracker', () => {
  it('does not turn a forward seek into watched coverage', () => {
    const tracker = new WatchedRangeTracker();
    tracker.setPlaying(true);
    tracker.sample(0); tracker.sample(15);
    tracker.markSeeking(); tracker.sample(598); tracker.sample(600);
    expect(tracker.snapshot()).toEqual([[0, 15], [598, 600]]);
    expect(tracker.frontier()).toBe(15);
  });

  it('merges contiguous natural watch coverage', () => {
    expect(contiguousFrontier([[0, 50], [50.2, 99]])).toBe(99);
  });

  it('restores verified coverage without turning a later seek into coverage', () => {
    const tracker = new WatchedRangeTracker();
    tracker.restore([[0, 30]]);
    tracker.setPlaying(true);
    tracker.markSeeking(); tracker.sample(80); tracker.sample(82);
    expect(tracker.snapshot()).toEqual([[0, 30], [80, 82]]);
    expect(tracker.frontier()).toBe(30);
  });
});

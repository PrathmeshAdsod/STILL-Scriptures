export type Range = [number, number];

export function mergeRanges(input: Range[], epsilon = 0.25): Range[] {
  const ordered = input.filter(([start, end]) => end > start).sort(([a], [b]) => a - b);
  return ordered.reduce<Range[]>((result, [start, end]) => {
    const previous = result.at(-1);
    if (!previous || start > previous[1] + epsilon) result.push([start, end]);
    else previous[1] = Math.max(previous[1], end);
    return result;
  }, []);
}

export function contiguousFrontier(ranges: Range[], tolerance = 1): number {
  return mergeRanges(ranges).reduce((frontier, [start, end]) => start <= frontier + tolerance ? Math.max(frontier, end) : frontier, 0);
}

export class WatchedRangeTracker {
  private ranges: Range[] = [];
  private lastTime?: number;
  private playing = false;
  private seeking = false;
  restore(ranges: Range[]) { this.ranges = mergeRanges(ranges); this.lastTime = undefined; this.seeking = false; }
  setPlaying(playing: boolean) { this.playing = playing; if (!playing) this.lastTime = undefined; }
  markSeeking() { this.seeking = true; this.lastTime = undefined; }
  sample(currentTime: number, playbackRate = 1) {
    if (this.playing && !this.seeking && this.lastTime !== undefined) {
      // Browsers can pause event delivery while a tab is backgrounded; an explicit seek event,
      // not a short timer gap, is the authoritative signal that coverage must be broken.
      const maxExpectedJump = Math.max(20, playbackRate * 20);
      if (currentTime >= this.lastTime && currentTime - this.lastTime <= maxExpectedJump) this.ranges = mergeRanges([...this.ranges, [this.lastTime, currentTime]]);
    }
    this.lastTime = currentTime;
    this.seeking = false;
  }
  snapshot(): Range[] { return this.ranges.map(([start, end]) => [start, end]); }
  frontier(): number { return contiguousFrontier(this.ranges); }
}

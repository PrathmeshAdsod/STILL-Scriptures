import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { YouTubePlaybackAdapter } from './YouTubePlaybackAdapter';

type PlayerOptions = { events: { onReady: () => void; onStateChange: (event: { data: number }) => void } };

class FakeYouTubePlayer {
  static latest?: FakeYouTubePlayer;
  currentTime = 0;

  constructor(_element: HTMLElement, options: PlayerOptions) {
    FakeYouTubePlayer.latest = this;
    options.events.onReady();
  }

  loadVideoById() {}
  playVideo() {}
  pauseVideo() {}
  seekTo(seconds: number) { this.currentTime = seconds; }
  getCurrentTime() { return this.currentTime; }
  getDuration() { return 259; }
  getPlaybackRate() { return 1; }
  destroy() {}
}

describe('YouTubePlaybackAdapter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.defineProperty(window, 'YT', {
      configurable: true,
      value: { Player: FakeYouTubePlayer, PlayerState: { PLAYING: 1, ENDED: 0 } },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    Reflect.deleteProperty(window, 'YT');
    FakeYouTubePlayer.latest = undefined;
  });

  it('observes a playhead scrub while the embed is paused', async () => {
    const adapter = new YouTubePlaybackAdapter(document.createElement('div'));
    const observed: number[] = [];
    adapter.onTimeUpdate((seconds) => observed.push(seconds));
    await adapter.load('video-id');

    FakeYouTubePlayer.latest!.currentTime = 211;
    await vi.advanceTimersByTimeAsync(500);

    expect(observed).toEqual([211]);
    adapter.destroy();
  });
});

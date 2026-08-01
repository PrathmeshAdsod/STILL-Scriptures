import type { PlaybackAdapter, PlaybackState } from './PlaybackAdapter';

declare global { interface Window { YT?: { Player: new (element: HTMLElement, options: object) => YouTubePlayer; PlayerState: Record<string, number> }; onYouTubeIframeAPIReady?: () => void } }
interface YouTubePlayer { loadVideoById(id: string): void; playVideo(): void; pauseVideo(): void; seekTo(seconds: number, allowSeekAhead: boolean): void; getCurrentTime(): number; getDuration(): number; getPlaybackRate(): number; destroy(): void; }

export class YouTubePlaybackAdapter implements PlaybackAdapter {
  private player?: YouTubePlayer;
  private current = 0;
  private timer?: number;
  private timeListeners = new Set<(seconds: number) => void>();
  private seekListeners = new Set<(seconds: number) => void>();
  private stateListeners = new Set<(state: PlaybackState) => void>();
  private endedListeners = new Set<() => void>();
  constructor(private readonly element: HTMLElement) {}
  async load(videoId: string) {
    await this.ensureApi();
    await new Promise<void>((resolve) => {
      this.player = new window.YT!.Player(this.element, { videoId, playerVars: { rel: 0, modestbranding: 1 }, events: {
        onReady: () => { this.startTicker(); resolve(); },
        onStateChange: (event: { data: number }) => this.handleState(event.data),
      }});
    });
  }
  async play() { this.player?.playVideo(); }
  pause() { this.player?.pauseVideo(); }
  seek(seconds: number) { this.player?.seekTo(seconds, true); this.seekListeners.forEach((listener) => listener(seconds)); }
  getCurrentTime() { return this.player?.getCurrentTime() ?? this.current; }
  getDuration() { return this.player?.getDuration() ?? 0; }
  getPlaybackRate() { return this.player?.getPlaybackRate() ?? 1; }
  onTimeUpdate(listener: (seconds: number) => void) { this.timeListeners.add(listener); return () => this.timeListeners.delete(listener); }
  onSeek(listener: (seconds: number) => void) { this.seekListeners.add(listener); return () => this.seekListeners.delete(listener); }
  onStateChange(listener: (state: PlaybackState) => void) { this.stateListeners.add(listener); return () => this.stateListeners.delete(listener); }
  onEnded(listener: () => void) { this.endedListeners.add(listener); return () => this.endedListeners.delete(listener); }
  destroy() { if (this.timer) window.clearInterval(this.timer); this.player?.destroy(); }
  private handleState(code: number) {
    const state = window.YT?.PlayerState;
    const mapped: PlaybackState = code === state?.PLAYING ? 'playing' : code === state?.ENDED ? 'ended' : 'paused';
    this.stateListeners.forEach((listener) => listener(mapped));
    if (mapped === 'ended') this.endedListeners.forEach((listener) => listener());
  }
  private startTicker() { if (this.timer) return; this.timer = window.setInterval(() => { this.current = this.getCurrentTime(); this.timeListeners.forEach((listener) => listener(this.current)); }, 500); }
  private ensureApi(): Promise<void> {
    if (window.YT?.Player) return Promise.resolve();
    return new Promise((resolve) => {
      const script = document.createElement('script'); script.src = 'https://www.youtube.com/iframe_api'; document.head.append(script);
      window.onYouTubeIframeAPIReady = () => resolve();
    });
  }
}

import type { PlaybackAdapter, PlaybackState } from './PlaybackAdapter';

export class Html5PlaybackAdapter implements PlaybackAdapter {
  constructor(private readonly video: HTMLVideoElement) {}
  async load(source: string) { this.video.src = source; this.video.load(); }
  async play() { await this.video.play(); }
  pause() { this.video.pause(); }
  seek(seconds: number) { this.video.currentTime = seconds; }
  getCurrentTime() { return this.video.currentTime; }
  getDuration() { return this.video.duration || 0; }
  getPlaybackRate() { return this.video.playbackRate; }
  onTimeUpdate(listener: (seconds: number) => void) { const handler = () => listener(this.video.currentTime); this.video.addEventListener('timeupdate', handler); return () => this.video.removeEventListener('timeupdate', handler); }
  onSeek(listener: (seconds: number) => void) { const handler = () => listener(this.video.currentTime); this.video.addEventListener('seeking', handler); return () => this.video.removeEventListener('seeking', handler); }
  onStateChange(listener: (state: PlaybackState) => void) { const handler = () => listener(this.video.ended ? 'ended' : this.video.paused ? 'paused' : 'playing'); this.video.addEventListener('play', handler); this.video.addEventListener('pause', handler); return () => { this.video.removeEventListener('play', handler); this.video.removeEventListener('pause', handler); }; }
  onEnded(listener: () => void) { this.video.addEventListener('ended', listener); return () => this.video.removeEventListener('ended', listener); }
  destroy() { this.video.pause(); this.video.removeAttribute('src'); this.video.load(); }
}

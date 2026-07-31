export type PlaybackState = 'idle' | 'playing' | 'paused' | 'ended';

export interface PlaybackAdapter {
  load(source: string): Promise<void>;
  play(): Promise<void>;
  pause(): void;
  seek(seconds: number): void;
  getCurrentTime(): number;
  getDuration(): number;
  getPlaybackRate(): number;
  onTimeUpdate(listener: (seconds: number) => void): () => void;
  onSeek(listener: (seconds: number) => void): () => void;
  onStateChange(listener: (state: PlaybackState) => void): () => void;
  onEnded(listener: () => void): () => void;
  destroy(): void;
}

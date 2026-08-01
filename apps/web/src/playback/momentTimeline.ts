export function timelinePercent(seconds: number, durationSeconds: number) {
  if (!Number.isFinite(seconds) || !Number.isFinite(durationSeconds) || durationSeconds <= 0) return 0;
  return Math.min(100, Math.max(0, (seconds / durationSeconds) * 100));
}

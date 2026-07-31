export async function sha256(file: File): Promise<string> {
  const data = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function inspectVideo(file: File): Promise<{ duration: number; hasAudio?: boolean; hasVideo: boolean }> {
  const objectUrl = URL.createObjectURL(file);
  try {
    return await new Promise((resolve, reject) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadedmetadata = () => {
        const hasVideo = video.videoWidth > 0 && video.videoHeight > 0;
        // Browser metadata exposes video dimensions reliably; actual audio track validation remains server-side/FFmpeg in deployment.
        resolve({ duration: video.duration, hasVideo });
      };
      video.onerror = () => reject(new Error('The selected file could not be read as a supported video.'));
      video.src = objectUrl;
    });
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export function youtubeId(input: string): string | undefined {
  try {
    const url = new URL(input);
    if (url.hostname === 'youtu.be') return url.pathname.slice(1);
    return url.searchParams.get('v') ?? undefined;
  } catch {
    return undefined;
  }
}

export async function inspectYoutube(url: string): Promise<{ id: string; duration: number }> {
  const id = youtubeId(url);
  if (!id) throw new Error('Enter a public YouTube watch link.');
  const youtubeWindow = window as unknown as { YT?: { Player: new (element: HTMLElement, options: object) => { getDuration(): number; destroy(): void } }; onYouTubeIframeAPIReady?: () => void };
  if (!youtubeWindow.YT?.Player) {
    await new Promise<void>((resolve, reject) => {
      const oldReady = youtubeWindow.onYouTubeIframeAPIReady;
      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      script.onerror = () => reject(new Error('YouTube could not be reached to validate this story.'));
      youtubeWindow.onYouTubeIframeAPIReady = () => { oldReady?.(); resolve(); };
      document.head.append(script);
    });
  }
  const holder = document.createElement('div');
  holder.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;left:-9999px';
  document.body.append(holder);
  try {
    return await new Promise((resolve, reject) => {
      const player = new youtubeWindow.YT!.Player(holder, {
        videoId: id,
        events: { onReady: () => { const duration = player.getDuration(); player.destroy(); if (duration > 0) resolve({ id, duration }); else reject(new Error('This public YouTube video did not return a duration.')); } },
      });
    });
  } finally {
    holder.remove();
  }
}

import { useEffect, useState, type FormEvent } from 'react';
import { api } from './lib/api';
import { clientConfig, firebaseConfigured } from './lib/config';
import { inspectVideo, inspectYoutube, sha256, youtubeId } from './lib/source';
import { observeFirebaseUser, signInToStill, uploadVideo } from './lib/firebase';
import { Html5PlaybackAdapter } from './playback/Html5PlaybackAdapter';
import type { PlaybackAdapter } from './playback/PlaybackAdapter';
import { YouTubePlaybackAdapter } from './playback/YouTubePlaybackAdapter';
import { WatchedRangeTracker } from './playback/WatchedRangeTracker';
import type { Echo, Project, ViewingSession } from './types';

type Route = { page: 'home' | 'add' | 'processing' | 'watch' | 'reflect'; projectId?: string };
const sourceKey = (id: string) => `still:playback-source:${id}`;
const sessionKey = (id: string) => `still:session:${id}`;

function parseRoute(): Route {
  const [page = 'home', projectId] = location.hash.replace(/^#\/?/, '').split('/');
  return ['add', 'processing', 'watch', 'reflect'].includes(page) ? { page: page as Route['page'], projectId } : { page: 'home' };
}
function go(path: string) { location.hash = path; }
function showHowItWorks() {
  const scroll = () => document.getElementById('principle')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (parseRoute().page === 'home') scroll();
  else { go('/'); window.setTimeout(scroll, 50); }
}
function useRoute(): Route {
  const [route, setRoute] = useState(parseRoute);
  useEffect(() => { const listener = () => setRoute(parseRoute()); addEventListener('hashchange', listener); return () => removeEventListener('hashchange', listener); }, []);
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'auto' }); }, [route.page, route.projectId]);
  return route;
}

function Mark() { return <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>; }
function Header({ quiet = false }: { quiet?: boolean }) {
  const [signedIn, setSignedIn] = useState(false);
  const [authError, setAuthError] = useState<string>();
  useEffect(() => observeFirebaseUser((user) => setSignedIn(Boolean(user))), []);
  async function handleAccount() {
    if (signedIn) return;
    try { setAuthError(undefined); await signInToStill(); }
    catch (error) { setAuthError(error instanceof Error ? error.message : 'Sign-in could not be completed.'); }
  }
  return <header className={`site-header ${quiet ? 'quiet' : ''}`}>
    <button className="wordmark" onClick={() => go('/')} aria-label="STILL home"><Mark />STILL</button>
    <nav aria-label="Primary navigation"><button onClick={() => go('/add')}>Add story</button><button onClick={showHowItWorks}>How it works</button></nav>
    <button className="account-button" aria-label={clientConfig.publicShowcase ? 'Public competition preview' : signedIn ? 'Signed in account' : 'Sign in'} onClick={handleAccount} disabled={clientConfig.publicShowcase}><span>◌</span><b>{clientConfig.publicShowcase ? 'Public preview' : signedIn ? 'Account' : 'Sign in'}</b></button>
    {authError && <p className="auth-error" role="alert">{authError}</p>}
  </header>;
}

function Landing() {
  return <main className="landing">
    <Header />
    <section className="hero-grid">
      <aside className="hero-index"><span>01 / 03</span><div><i /><i /></div><p>A quiet system<br />for watching well.</p></aside>
      <div className="hero-copy">
        <p className="eyebrow">A SPOILER-SAFE REFLECTION LAYER</p>
        <h1>Let the story land<br />before it <em>speaks back.</em></h1>
        <p className="hero-summary">STILL meets you when a scene becomes meaningful—<br className="desktop-only" /> without pulling you ahead of the story.</p>
        <button className="primary-action" onClick={() => go('/add')}><span>＋</span> Add a story <b>→</b></button>
        <p className="microcopy">WATCH FIRST. REFLECT WHEN YOU ARE READY.</p>
      </div>
      <div className="hero-orbit" aria-hidden="true"><div className="orbit-ring" /><span>THE<br />STILL<br />POINT</span><b>00:37</b></div>
    </section>
    <section className="current-card" aria-label="How spoiler safety works">
      <div><p className="eyebrow">YOUR STORY REMAINS YOURS</p><h2>No emotional spoilers.</h2><span>Only a quiet marker when a moment is ready.</span></div>
      <div className="progress-story"><p className="eyebrow">THE CURRENT</p><div className="story-track"><i /><b /></div><small>00:37 watched</small><small>reflection held</small></div>
      <div><p className="eyebrow">THE PROMISE</p><h2>Meaning, never premature.</h2><span>Your watched frontier is the boundary.</span></div>
    </section>
    <section className="landing-detail" id="principle">
      <div className="detail-copy"><p className="eyebrow blue">A DIFFERENT KIND OF VIDEO LIBRARY</p><h2>Designed for the pause<br />after the scene.</h2><p>STILL holds the context, the questions, and the right timing. It is deliberately quiet while the story is still unfolding.</p><button className="text-link" onClick={() => go('/add')}>Begin with your story <b>↗</b></button></div>
      <div className="observation-card" aria-label="A sample observation card">
        <div className="card-browser"><span /><span /><span /><b>THE QUIET ROOM / 00:37</b></div>
        <div className="observation-body"><div className="scene-illustration"><i className="hill" /><i className="person one" /><i className="person two" /></div><div className="observation-text"><p className="eyebrow">OBSERVED, NOT INTERPRETED</p><blockquote>“The room laughs, but he<br />does not look amused.”</blockquote><div><span /> Reflection held until watched</div></div></div>
      </div>
    </section>
    <footer><span>STILL / V1</span><p>A spoiler-safe reflection layer for video.</p><div aria-label="Product principles"><span>Private by design</span><span>No forced reflection</span></div></footer>
  </main>;
}

function AddStory() {
  const [sourceType, setSourceType] = useState<'upload' | 'youtube'>('upload');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File>();
  const [youtube, setYoutube] = useState('');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number>();
  const [error, setError] = useState<string>();
  const canSubmit = !clientConfig.publicShowcase && Boolean(title.trim() && (sourceType === 'upload' ? file : youtube));
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!canSubmit) return;
    setBusy(true); setError(undefined);
    try {
      const created = await api.createProject(title.trim());
      if (sourceType === 'upload' && file) {
        const [media, hash] = await Promise.all([inspectVideo(file), sha256(file)]);
        const uploaded = await uploadVideo(file, created.project_id, setProgress);
        sessionStorage.setItem(sourceKey(created.project_id), uploaded.playbackUrl);
        await api.completeUpload(created.project_id, { storage_path: uploaded.storagePath, original_filename: file.name, content_type: file.type, size_bytes: file.size, sha256: hash, duration_seconds: media.duration, has_video: media.hasVideo });
      } else if (sourceType === 'youtube') {
        const metadata = await inspectYoutube(youtube);
        await api.setYoutubeSource(created.project_id, youtube, title.trim(), metadata.duration);
      }
      await api.startAnalysis(created.project_id);
      go(`/processing/${created.project_id}`);
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'This story could not be added.'); } finally { setBusy(false); }
  }
  return <main className="app-shell"><Header quiet /><section className="source-page"><div className="source-intro"><p className="eyebrow blue">NEW STORY</p><h1>Give the story<br />its first quiet room.</h1><p>Upload a video you own or choose a public YouTube story. STILL prepares it once, then stays out of the way.</p><div className="source-notes"><span>◌ Your video stays private to your project.</span><span>◌ Processing can continue after you leave.</span><span>◌ No reflection is created from title alone.</span></div></div><form className="source-form" onSubmit={submit}>
      {clientConfig.publicShowcase && <p className="showcase-note">This public Spark-hosted preview keeps provider credentials off the browser. The real audiovisual run is shown in the competition demo and documented in the repository.</p>}
      <div className="source-tabs" role="tablist"><button type="button" className={sourceType === 'upload' ? 'selected' : ''} onClick={() => setSourceType('upload')}>Upload a video</button><button type="button" className={sourceType === 'youtube' ? 'selected' : ''} onClick={() => setSourceType('youtube')}>Public YouTube URL</button></div>
      <label>Story title<input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="A name you will recognise" maxLength={180} required /></label>
      {sourceType === 'upload' ? <label className="file-drop"><input type="file" accept="video/mp4,video/webm,video/quicktime,video/mpeg" onChange={(e) => { const selected = e.target.files?.[0]; setFile(selected); if (selected && !title) setTitle(selected.name.replace(/\.[^/.]+$/, '')); }} required /><span className="upload-glyph">↑</span><strong>{file?.name ?? 'Choose a video file'}</strong><small>{file ? `${Math.round(file.size / 1024 / 1024)} MB` : 'MP4, WebM, MOV, MPEG'}</small></label> : <label>Public YouTube link<input value={youtube} onChange={(e) => setYoutube(e.target.value)} placeholder="https://www.youtube.com/watch?v=…" inputMode="url" required /><small>STILL validates public playback before processing. It never downloads YouTube video.</small></label>}
      {progress !== undefined && <div className="upload-progress"><i style={{ transform: `scaleX(${progress})` }} /><span>Uploading {Math.round(progress * 100)}%</span></div>}
      {!firebaseConfigured && sourceType === 'upload' && <p className="form-warning">Firebase Storage is not configured in this environment, so upload remains unavailable rather than simulated.</p>}
      {error && <p role="alert" className="form-error">{error}</p>}
      <button className="primary-action wide" disabled={!canSubmit || busy}>{clientConfig.publicShowcase ? 'Interactive run shown in demo' : busy ? 'Preparing your story…' : 'Prepare this story'} <b>→</b></button>
      {clientConfig.publicShowcase && <a className="showcase-link" href={clientConfig.githubUrl} target="_blank" rel="noreferrer">Explore the implementation <b>↗</b></a>}
      <p className="form-fineprint">By continuing, you confirm you own the video or have the right to use it.</p>
    </form></section></main>;
}

function stageCopy(project: Project) {
  const copy: Record<string, [string, string]> = { source_received: ['Story received.', 'Checking the source before anything is understood.'], preparing_media: ['Preparing the story.', 'Registering one reusable source for bounded analysis.'], understanding_story: ['Understanding the story.', 'Following it in order without looking ahead.'], grounding_reflection: ['Holding the right moments.', 'Only grounded reflections can pass this point.'], ready: ['Your story is ready.', 'Nothing will interrupt the first watch.'], failed: ['Analysis is unavailable.', 'Nothing has been invented or substituted.'] };
  return copy[project.progress.stage] ?? ['Preparing your story.', 'This project can continue in the background.'];
}

function Processing({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project>();
  const [error, setError] = useState<string>();
  const [retrying, setRetrying] = useState(false);
  useEffect(() => { let active = true; const poll = async () => { try { const status = await api.getStatus(projectId); if (active) { setProject(status); setError(undefined); } } catch (caught) { if (active) setError(caught instanceof Error ? caught.message : 'Unable to read project status.'); } }; void poll(); const timer = window.setInterval(() => void poll(), 3500); return () => { active = false; clearInterval(timer); }; }, [projectId]);
  const [heading, detail] = project ? stageCopy(project) : ['Finding your story.', 'Connecting to its preparation state.'];
  const percentage = project?.progress.total_windows ? Math.round((project.progress.completed_windows / project.progress.total_windows) * 100) : undefined;
  async function retry() { setRetrying(true); setError(undefined); try { await api.startAnalysis(projectId); } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to retry analysis.'); } finally { setRetrying(false); } }
  const ready = project?.status === 'READY' || project?.status === 'READY_NO_ECHO';
  const failed = project?.status === 'FAILED_RETRIABLE' || project?.status === 'FAILED';
  const retriable = project?.status === 'FAILED_RETRIABLE';
  return <main className="app-shell processing-shell"><Header quiet /><section className="processing"><div className="processing-pulse"><i /><i /><i /><i /></div><p className="eyebrow blue">STORY PREPARATION</p><h1>{heading}</h1><p>{detail}</p><div className="process-line"><i style={{ width: percentage === undefined ? '18%' : `${percentage}%` }} /></div>{percentage === undefined ? <small>Progress will appear as real bounded windows complete.</small> : <small>{project?.progress.completed_windows} of {project?.progress.total_windows} causal windows complete</small>}
    {ready && <button className="primary-action" onClick={() => go(`/watch/${projectId}`)}>Begin watching <b>→</b></button>}
    {failed && <div className="failure-card"><strong>We could not complete the analysis.</strong><p>{project?.failure_message ?? 'The provider is temporarily unavailable. No reflection has been generated.'}</p>{retriable ? <button className="secondary-action" onClick={() => void retry()} disabled={retrying}>{retrying ? 'Retrying…' : 'Retry preparation'}</button> : <button className="secondary-action" onClick={() => go('/add')}>Choose another source</button>}</div>}
    {error && <p className="form-error" role="alert">{error}</p>}<p className="processing-note">You can safely leave this page. STILL never fabricates a result while a provider is unavailable.</p></section></main>;
}

function formatTime(seconds: number) { const total = Math.max(0, Math.floor(seconds)); return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`; }

function Watch({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project>(); const [session, setSession] = useState<ViewingSession>(); const [echoes, setEchoes] = useState<Echo[]>([]); const [showReflections, setShowReflections] = useState(false); const [playerState, setPlayerState] = useState<'idle' | 'playing' | 'paused' | 'ended'>('idle'); const [time, setTime] = useState(0); const [error, setError] = useState<string>();
  const videoRef = useState(() => ({ current: null as HTMLVideoElement | null }))[0]; const youtubeRef = useState(() => ({ current: null as HTMLDivElement | null }))[0]; const adapterRef = useState(() => ({ current: undefined as PlaybackAdapter | undefined }))[0]; const trackerRef = useState(() => new WatchedRangeTracker())[0];
  const source = project?.source; const sourceUrl = sessionStorage.getItem(sourceKey(projectId)); const sessionId = session?.id;
  useEffect(() => { let active = true; void (async () => { try { const loaded = await api.getProject(projectId); const sessionId = sessionStorage.getItem(sessionKey(projectId)); const started = sessionId ? { session_id: sessionId } : await api.createSession(projectId); if (!sessionId) sessionStorage.setItem(sessionKey(projectId), started.session_id); if (active) { setProject(loaded.project); setSession({ id: started.session_id, project_id: projectId, watched_ranges: [], contiguous_frontier_seconds: 0, story_complete: false, ended_naturally: false }); } } catch (caught) { if (active) setError(caught instanceof Error ? caught.message : 'This watch session could not start.'); } })(); return () => { active = false; }; }, [projectId]);
  useEffect(() => { if (!source || !sessionId) return; let disposed = false; const setup = async () => { try { let adapter: PlaybackAdapter; if (source.kind === 'youtube' && source.public_url && youtubeRef.current) { adapter = new YouTubePlaybackAdapter(youtubeRef.current); await adapter.load(youtubeId(source.public_url) ?? ''); } else if (source.kind === 'upload' && sourceUrl && videoRef.current) { adapter = new Html5PlaybackAdapter(videoRef.current); await adapter.load(sourceUrl); } else { setError('Playback requires the original authorized source. No substitute media is shown.'); return; } if (disposed) { adapter.destroy(); return; } adapterRef.current = adapter; const sync = async (endedNaturally = false) => { if (!sessionId || !source.duration_seconds) return; try { const next = await api.updateSession(projectId, sessionId, { ranges: trackerRef.snapshot(), duration_seconds: source.duration_seconds, ended_naturally: endedNaturally }); if (!disposed) setSession(next); } catch (caught) { if (!disposed) setError(caught instanceof Error ? caught.message : 'Watch progress could not be saved.'); } }; const unsubscribe = [adapter.onTimeUpdate((value) => { trackerRef.sample(value, adapter.getPlaybackRate()); setTime(value); if (Math.floor(value) % 12 === 0) void sync(); }), adapter.onSeek(() => trackerRef.markSeeking()), adapter.onStateChange((state) => { trackerRef.setPlaying(state === 'playing'); setPlayerState(state); if (state === 'paused') void sync(); }), adapter.onEnded(() => void sync(true))]; return () => unsubscribe.forEach((off) => off()); } catch (caught) { if (!disposed) setError(caught instanceof Error ? caught.message : 'Playback could not be loaded.'); } }; let teardown: (() => void) | undefined; void setup().then((result) => { teardown = result; }); return () => { disposed = true; teardown?.(); adapterRef.current?.destroy(); adapterRef.current = undefined; }; }, [adapterRef, projectId, sessionId, source, sourceUrl, trackerRef, videoRef, youtubeRef]);
  useEffect(() => { if (!showReflections || !session) return; void api.getEchoes(projectId, session.id).then(setEchoes).catch((caught) => setError(caught instanceof Error ? caught.message : 'Reflections are unavailable.')); }, [projectId, session, showReflections]);
  if (!project || !source) return <main className="app-shell"><Header quiet /><div className="center-message">Opening the quiet room…</div></main>;
  return <main className="watch-shell"><Header quiet /><section className="watch-header"><p className="eyebrow blue">FIRST WATCH</p><h1>{project.title}</h1><span>{formatTime(time)} / {formatTime(source.duration_seconds ?? 0)}</span></section><section className="watch-stage"><div className="video-frame">{source.kind === 'youtube' ? <div ref={(node) => { youtubeRef.current = node; }} className="youtube-frame" title="YouTube story" /> : <video ref={(node) => { videoRef.current = node; }} controls playsInline preload="metadata" aria-label={`Video: ${project.title}`} />}<div className="video-corner top">STILL / FIRST WATCH</div><div className="video-corner bottom">{playerState === 'playing' ? 'PLAYING' : 'QUIETLY WAITING'}</div></div><aside className="watch-aside"><p className="eyebrow">YOUR FRONTIER</p><strong>{formatTime(session?.contiguous_frontier_seconds ?? 0)}</strong><span>Only this much story can inform what you see below.</span><button className="secondary-action" onClick={() => void adapterRef.current?.play()}>Continue story <b>→</b></button></aside></section><section className="quiet-reflection"><button className="reflection-toggle" onClick={() => { setShowReflections((current) => !current); adapterRef.current?.pause(); }} aria-expanded={showReflections}><span><i /> Reflections so far</span><b>{showReflections ? '−' : '+'}</b></button>{showReflections && <div className="reflection-drawer">{echoes.length ? echoes.map((echo) => <article className="early-echo" key={echo.id}><p className="timestamp">{formatTime(echo.knowledge_cutoff_seconds)}</p><h2>{echo.tension}</h2><p>{echo.scene_context}</p><button className="text-link" onClick={() => { adapterRef.current?.pause(); }}>Pause with this moment <b>↗</b></button></article>) : <p className="empty-reflection">Nothing has been offered for the portion you have watched. STILL is comfortable with silence.</p>}</div>}</section>{session?.story_complete && <section className="story-complete"><p className="eyebrow blue">STORY COMPLETE</p><h2>The whole story has room to breathe now.</h2><p>You watched it through. Full reflections can now include the complete arc without spoiling it.</p><button className="primary-action" onClick={() => go(`/reflect/${projectId}`)}>Enter reflection <b>→</b></button></section>}{error && <p className="watch-error" role="alert">{error}</p>}</main>;
}

function Reflect({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project>(); const [echoes, setEchoes] = useState<Echo[]>(); const [error, setError] = useState<string>();
  useEffect(() => { const sessionId = sessionStorage.getItem(sessionKey(projectId)); if (!sessionId) { setError('Return to the story and finish watching before opening full reflection.'); return; } void Promise.all([api.getProject(projectId), api.getStoryReflection(projectId, sessionId)]).then(([loaded, reflection]) => { setProject(loaded.project); setEchoes(reflection); }).catch((caught) => setError(caught instanceof Error ? caught.message : 'Full reflection is not available yet.')); }, [projectId]);
  return <main className="reflect-shell"><Header quiet /><section className="reflect-intro"><p className="eyebrow blue">AFTER THE STORY</p><h1>{project?.title ?? 'Reflection'}</h1><p>These moments are grounded in the complete story you watched. Scripture is shown only when retrieved with its version and attribution.</p></section>{error && <p className="form-error reflect-error" role="alert">{error}</p>}{echoes?.length === 0 && <section className="no-echo"><p className="eyebrow">STILL REMAINED QUIET</p><h2>No Scripture Echo was forced into this story.</h2><p>That is a complete result, not a missing one.</p><button className="secondary-action" onClick={() => go(`/watch/${projectId}`)}>Return to story</button></section>}<section className="echo-list">{echoes?.map((echo, index) => <article className="full-echo" key={echo.id}><div className="echo-number">0{index + 1}</div><div><p className="timestamp">A moment at {formatTime(echo.knowledge_cutoff_seconds)}</p><h2>{echo.tension}</h2><p className="scene-context">{echo.scene_context}</p>{echo.exact_scripture_text && <figure><blockquote>{echo.exact_scripture_text}</blockquote><figcaption>{echo.scripture_reference} {echo.bible_version ? `· ${echo.bible_version}` : ''}</figcaption><small>{echo.copyright_attribution}</small></figure>}{echo.connection_explanation && <p className="connection">{echo.connection_explanation}</p>}</div></article>)}</section></main>;
}

export default function App() { const route = useRoute(); if (route.page === 'add') return <AddStory />; if (route.page === 'processing' && route.projectId) return <Processing projectId={route.projectId} />; if (route.page === 'watch' && route.projectId) return <Watch projectId={route.projectId} />; if (route.page === 'reflect' && route.projectId) return <Reflect projectId={route.projectId} />; return <Landing />; }

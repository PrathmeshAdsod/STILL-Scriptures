import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import type { User } from 'firebase/auth';
import { api } from './lib/api';
import { clientConfig, firebaseConfigured } from './lib/config';
import {
  createStillAccount,
  observeFirebaseUser,
  refreshStillUser,
  resendStillVerification,
  sendStillPasswordReset,
  signInToStill,
  signOutOfStill,
} from './lib/firebase';
import { inspectYoutube, youtubeId } from './lib/source';
import { Html5PlaybackAdapter } from './playback/Html5PlaybackAdapter';
import type { PlaybackAdapter } from './playback/PlaybackAdapter';
import { YouTubePlaybackAdapter } from './playback/YouTubePlaybackAdapter';
import { WatchedRangeTracker } from './playback/WatchedRangeTracker';
import type { AccountStatus, Echo, Project, ProjectLibraryItem, ViewingSession } from './types';

type Route = { page: 'home' | 'add' | 'auth' | 'plans' | 'account' | 'library' | 'processing' | 'watch' | 'reflect'; projectId?: string };
const sourceKey = (id: string) => `still:playback-source:${id}`;

function parseRoute(): Route {
  const [page = 'home', projectId] = location.hash.replace(/^#\/?/, '').split('/');
  return ['add', 'auth', 'plans', 'account', 'library', 'processing', 'watch', 'reflect'].includes(page)
    ? { page: page as Route['page'], projectId }
    : { page: 'home' };
}

function go(path: string) { location.hash = path; }

function showHowItWorks() {
  const scroll = () => document.getElementById('principle')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (parseRoute().page === 'home') scroll();
  else { go('/'); window.setTimeout(scroll, 50); }
}

function useRoute(): Route {
  const [route, setRoute] = useState(parseRoute);
  useEffect(() => {
    const listener = () => setRoute(parseRoute());
    addEventListener('hashchange', listener);
    return () => removeEventListener('hashchange', listener);
  }, []);
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'auto' }); }, [route.page, route.projectId]);
  return route;
}

function useFirebaseUser(): { user: User | null; loading: boolean } {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => observeFirebaseUser((next) => { setUser(next); setLoading(false); }), []);
  return { user, loading };
}

function Mark() { return <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>; }

function Header({ quiet = false }: { quiet?: boolean }) {
  const { user } = useFirebaseUser();
  return <header className={`site-header ${quiet ? 'quiet' : ''}`}>
    <button className="wordmark" onClick={() => go('/')} aria-label="STILL home"><Mark />STILL</button>
    <nav aria-label="Primary navigation">
      <button onClick={() => go('/add')}>Analyze</button>
      <button onClick={() => go('/library')}>My videos</button>
      <button onClick={showHowItWorks}>How it works</button>
      <button onClick={() => go('/plans')}>Plans</button>
    </nav>
    <button className="account-button" aria-label={user ? 'Account' : 'Sign in'} onClick={() => go(user ? '/account' : '/auth')}>
      <span className={user ? 'account-dot active' : 'account-dot'} aria-hidden="true" />
      <b>{user ? 'Account' : 'Sign in'}</b>
    </button>
  </header>;
}

function Landing() {
  return <main className="landing">
    <Header />
    <section className="hero-grid">
      <aside className="hero-index"><span>01 / 03</span><div><i /><i /></div><p>A quiet system<br />for watching well.</p></aside>
      <div className="hero-copy">
        <p className="eyebrow">SPOILER-SAFE SCRIPTURE REFLECTION FOR VIDEO</p>
        <h1>Watch the story.<br />Meet Scripture at <em>the right moment.</em></h1>
        <p className="hero-summary">STILL watches in order, then reveals a grounded Bible reflection<br className="desktop-only" /> only after you reach the scene that supports it.</p>
        <button className="primary-action" onClick={() => go('/add')}><span>+</span> Analyze a video <b>→</b></button>
        <p className="microcopy">ONE REAL ANALYSIS ON FREE · VIDEOS UP TO SIX MINUTES</p>
      </div>
      <div className="hero-orbit" aria-hidden="true"><div className="orbit-ring" /><span>THE<br />STILL<br />POINT</span><b>00:37</b></div>
    </section>
    <section className="current-card" aria-label="How spoiler safety works">
      <div><p className="eyebrow">THE VIDEO STAYS PRIMARY</p><h2>No scene is spoiled.</h2><span>A reflection cannot appear before the moment that grounds it.</span></div>
      <div className="progress-story"><p className="eyebrow">YOUR WATCHED FRONTIER</p><div className="story-track"><i /><b /></div><small>00:37 watched</small><small>Scripture waiting</small></div>
      <div><p className="eyebrow">THE SCRIPTURE PROMISE</p><h2>Exact text. Honest timing.</h2><span>YouVersion passage, context, and attribution—never an AI-written verse.</span></div>
    </section>
    <section className="landing-detail" id="principle">
      <div className="detail-copy"><p className="eyebrow blue">FROM SCENE TO SCRIPTURE</p><h2>See the moment.<br />Open it when ready.</h2><p>Accepted reflections appear automatically at their grounded timestamps. You choose when to pause and open the scene context, exact passage, and why the connection fits.</p><button className="text-link" onClick={() => go('/add')}>Bring your story <b>↗</b></button></div>
      <div className="observation-card" aria-label="Example of a timed Scripture reflection">
        <div className="card-browser"><span /><span /><span /><b>TIMED REFLECTION / 03:20</b></div>
        <div className="observation-body"><div className="scene-illustration"><i className="hill" /><i className="person one" /><i className="person two" /></div><div className="observation-text"><p className="eyebrow">SCRIPTURE AVAILABLE</p><blockquote>A grounded reflection is ready for this moment.</blockquote><div><span /> Open context, exact passage, and connection</div></div></div>
      </div>
    </section>
    <footer><span>STILL / V1</span><p>Spoiler-safe Scripture reflection for video.</p><div aria-label="Product principles"><span>Exact canonical text</span><span>No forced reflection</span></div></footer>
  </main>;
}

type AuthMode = 'signin' | 'create' | 'reset';

function friendlyAuthError(error: unknown): string {
  const code = typeof error === 'object' && error && 'code' in error ? String(error.code) : '';
  if (code.includes('weak-password')) return 'Choose a stronger password with at least 12 characters.';
  if (code.includes('too-many-requests')) return 'Too many attempts. Please wait a moment and try again.';
  if (code.includes('network-request-failed')) return 'The authentication service could not be reached.';
  if (code.includes('email-already-in-use')) return 'An account already exists for this email. Sign in instead.';
  if (code.includes('invalid-email')) return 'Enter a valid email address.';
  return 'The email or password could not be accepted. Check the details and try again.';
}

function AuthPage() {
  const { user, loading } = useFirebaseUser();
  const [mode, setMode] = useState<AuthMode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();

  useEffect(() => {
    if (!loading && user?.emailVerified) go('/library');
  }, [loading, user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError(undefined); setNotice(undefined);
    try {
      if (mode === 'reset') {
        await sendStillPasswordReset(email);
        setNotice('If an account matches that email, a reset link is on its way.');
      } else if (mode === 'create') {
        await createStillAccount(email, password);
        setNotice('Account created. Open the verification email, then return here.');
      } else {
        const signedIn = await signInToStill(email, password);
        if (signedIn.emailVerified) go('/library');
        else setNotice('Your email still needs verification before a video can be analyzed.');
      }
    } catch (caught) { setError(friendlyAuthError(caught)); }
    finally { setBusy(false); }
  }

  if (loading) return <main className="app-shell"><Header quiet /><div className="center-message">Checking your account…</div></main>;
  if (user && !user.emailVerified) return <main className="app-shell"><Header quiet /><VerificationPanel user={user} /></main>;

  return <main className="app-shell"><Header quiet /><section className="auth-layout">
    <div className="source-intro"><p className="eyebrow blue">YOUR STILL ACCOUNT</p><h1>One account.<br />A protected quiet room.</h1><p>Email verification keeps real video processing available to people, while limiting automated abuse.</p><div className="source-notes"><span>○ Provider credentials never enter your browser.</span><span>○ Your plan is enforced by the server, not the page.</span><span>○ Password reset and verification are handled by Firebase.</span></div></div>
    <form className="source-form auth-form" onSubmit={submit}>
      <div className="auth-tabs" role="tablist" aria-label="Account action">
        <button type="button" className={mode === 'signin' ? 'selected' : ''} onClick={() => setMode('signin')}>Sign in</button>
        <button type="button" className={mode === 'create' ? 'selected' : ''} onClick={() => setMode('create')}>Create account</button>
      </div>
      <p className="eyebrow blue">{mode === 'reset' ? 'RESET PASSWORD' : mode === 'create' ? 'CREATE YOUR ACCOUNT' : 'WELCOME BACK'}</p>
      <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label>
      {mode !== 'reset' && <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={12} autoComplete={mode === 'create' ? 'new-password' : 'current-password'} required /><small>{mode === 'create' ? 'Use at least 12 characters.' : 'Your password stays with Firebase Authentication.'}</small></label>}
      {!firebaseConfigured && <p className="form-error" role="alert">Firebase Authentication is not configured in this environment.</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {notice && <p className="form-success" role="status">{notice}</p>}
      <button className="primary-action wide" disabled={!firebaseConfigured || !email.trim() || (mode !== 'reset' && password.length < 12) || busy}>{busy ? 'Please wait…' : mode === 'reset' ? 'Send reset link' : mode === 'create' ? 'Create account' : 'Sign in'} <b>→</b></button>
      <button type="button" className="text-link auth-reset" onClick={() => setMode(mode === 'reset' ? 'signin' : 'reset')}>{mode === 'reset' ? 'Return to sign in' : 'Forgot your password?'}</button>
    </form>
  </section></main>;
}

function VerificationPanel({ user }: { user: User }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  async function refresh() {
    setBusy(true); setMessage(undefined);
    try {
      const refreshed = await refreshStillUser();
      if (refreshed?.emailVerified) window.location.reload();
      else setMessage('Not verified yet. Open the email link, then check again.');
    } catch { setMessage('Verification status could not be refreshed.'); }
    finally { setBusy(false); }
  }
  async function resend() {
    setBusy(true); setMessage(undefined);
    try { await resendStillVerification(); setMessage('A fresh verification email has been sent.'); }
    catch { setMessage('The email could not be sent yet. Please wait and try again.'); }
    finally { setBusy(false); }
  }
  return <section className="single-card"><p className="eyebrow blue">VERIFY YOUR EMAIL</p><h1>Check your inbox.</h1><p>We sent a verification link to <strong>{user.email}</strong>. This one step protects the real analysis allowance from automated abuse.</p>{message && <p className="form-success" role="status">{message}</p>}<div className="button-row"><button className="primary-action" onClick={() => void refresh()} disabled={busy}>I have verified <b>→</b></button><button className="secondary-action" onClick={() => void resend()} disabled={busy}>Resend email</button></div><button className="text-link" onClick={() => void signOutOfStill()}>Use a different account</button></section>;
}

function Plans() {
  return <main className="app-shell"><Header quiet /><section className="plans-page"><div className="plans-intro"><p className="eyebrow blue">SIMPLE EARLY ACCESS</p><h1>Real analysis.<br />Clear limits.</h1><p>Every plan uses the same real audiovisual pipeline. The limits protect a young service from abuse and unexpected provider spend.</p></div><div className="plan-grid">
    <article className="plan-card"><p className="plan-label">FREE</p><h2>Begin with one story.</h2><p className="plan-price">$0 <small>during early access</small></p><ul><li>1 video analysis per account</li><li>Videos up to 6 minutes</li><li>Spoiler-safe first watch</li><li>Grounded reflection or an honest quiet result</li></ul><button className="primary-action wide" onClick={() => go('/add')}>Start free <b>→</b></button></article>
    <article className="plan-card featured"><p className="plan-label">ACCESS PASS · TESTING</p><h2>Continue with a private pass.</h2><p className="plan-price">10 <small>videos per day</small></p><ul><li>10 video analyses each UTC day during testing</li><li>Videos up to 6 minutes</li><li>The same full analysis pipeline</li><li>Activated with a private access code</li></ul><button className="secondary-action wide" onClick={() => go('/account')}>Enter access code <b>→</b></button></article>
  </div><p className="plans-note">Paid subscriptions are not available yet. There is no checkout, charge, or hidden payment flow in this release.</p></section></main>;
}

function AccountPage() {
  const { user, loading } = useFirebaseUser();
  const [account, setAccount] = useState<AccountStatus>();
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string>();
  useEffect(() => {
    if (user?.emailVerified) void api.getAccount().then(setAccount).catch((caught) => setError(caught instanceof Error ? caught.message : 'Account details are unavailable.'));
  }, [user]);
  async function redeem(event: FormEvent) {
    event.preventDefault();
    if (!code.trim() || busy) return;
    setBusy(true); setError(undefined);
    try { setAccount(await api.redeemAccessCode(code)); setCode(''); }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'The access code could not be applied.'); }
    finally { setBusy(false); }
  }
  async function deleteAccount() {
    if (deleting) return;
    setDeleting(true); setError(undefined);
    try {
      await api.deleteAccount();
      await signOutOfStill();
      for (const key of Object.keys(sessionStorage)) if (key.startsWith('still:')) sessionStorage.removeItem(key);
      go('/');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The account could not be deleted.');
      setDeleting(false);
    }
  }
  if (loading) return <main className="app-shell"><Header quiet /><div className="center-message">Checking your account…</div></main>;
  if (!user) return <main className="app-shell"><Header quiet /><SignInGate /></main>;
  if (!user.emailVerified) return <main className="app-shell"><Header quiet /><VerificationPanel user={user} /></main>;
  return <main className="app-shell"><Header quiet /><section className="account-page"><div className="account-heading"><p className="eyebrow blue">ACCOUNT</p><h1>Your quiet room.</h1><p>{user.email}</p></div><div className="account-grid">
    <article className="account-card"><div className="plan-status"><span>{account?.plan === 'ACCESS' ? 'ACCESS PASS' : 'FREE'}</span><i>{account?.plan === 'ACCESS' ? 'ACTIVE' : 'CURRENT PLAN'}</i></div><h2>{account ? `${account.analyses_remaining} of ${account.analysis_limit} analyses available` : 'Loading your allowance…'}</h2><p>{account?.usage_period === 'day' ? 'Your allowance resets at 00:00 UTC.' : 'The Free plan includes one real video analysis for this account.'}</p><div className="usage-meter"><i style={{ width: account ? `${Math.min(100, (account.analyses_used / account.analysis_limit) * 100)}%` : '0%' }} /></div><small>Maximum video length: 6 minutes</small><button className="primary-action wide" onClick={() => go('/add')} disabled={!account?.analyses_remaining}>Analyze a video <b>→</b></button></article>
    <form className="account-card access-form" onSubmit={redeem}><p className="eyebrow blue">PRIVATE ACCESS</p><h2>Have an Access Pass?</h2><p>Enter the private code you received. Codes are checked on the server and never stored in this browser.</p><label>Access code<input value={code} onChange={(event) => setCode(event.target.value)} autoComplete="off" spellCheck={false} required /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="secondary-action wide" disabled={!code.trim() || busy || account?.plan === 'ACCESS'}>{account?.plan === 'ACCESS' ? 'Access Pass active' : busy ? 'Applying…' : 'Apply access code'}</button></form>
  </div><div className="account-actions"><button className="text-link" onClick={() => go('/library')}>My videos</button><button className="text-link" onClick={() => void sendStillPasswordReset(user.email ?? '')}>Send password reset</button><button className="text-link danger" onClick={() => void signOutOfStill().then(() => go('/'))}>Sign out</button><button className="text-link danger" onClick={() => setConfirmDelete((current) => !current)}>Delete account</button></div>{confirmDelete && <section className="delete-account-panel" role="alert"><div><strong>Delete your account and every saved video?</strong><p>This permanently removes projects, analysis results, Echoes, and watch progress. It cannot be undone.</p></div><div className="button-row"><button className="danger-action" onClick={() => void deleteAccount()} disabled={deleting}>{deleting ? 'Deleting...' : 'Permanently delete'}</button><button className="secondary-action" onClick={() => setConfirmDelete(false)} disabled={deleting}>Keep my account</button></div></section>}</section></main>;
}

function SignInGate() {
  return <section className="single-card"><p className="eyebrow blue">ACCOUNT REQUIRED</p><h1>Sign in to analyze a story.</h1><p>A verified email account protects the real provider pipeline and keeps the Free allowance fair.</p><div className="button-row"><button className="primary-action" onClick={() => go('/auth')}>Sign in or create account <b>→</b></button><button className="secondary-action" onClick={() => go('/plans')}>View plans</button></div></section>;
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useFirebaseUser();
  if (loading) return <main className="app-shell"><Header quiet /><div className="center-message">Restoring your quiet room…</div></main>;
  if (!user) return <main className="app-shell"><Header quiet /><SignInGate /></main>;
  if (!user.emailVerified) return <main className="app-shell"><Header quiet /><VerificationPanel user={user} /></main>;
  return children;
}

const activeProjectStatuses: Project['status'][] = ['QUEUED', 'PREPARING', 'ANALYZING', 'GROUNDING'];

function projectDestination(project: Project, session?: ViewingSession): string {
  if (project.status === 'READY' || project.status === 'READY_NO_ECHO') {
    return session?.story_complete ? `/reflect/${project.id}` : `/watch/${project.id}`;
  }
  return `/processing/${project.id}`;
}

function libraryStatus(item: ProjectLibraryItem): { label: string; detail: string } {
  const { project, latest_session: session } = item;
  if (project.status === 'READY_NO_ECHO') return { label: 'ANALYSIS COMPLETE', detail: session?.story_complete ? 'Story completed. STILL remained quiet.' : 'Ready to watch. No Scripture was forced.' };
  if (project.status === 'READY') {
    if (session?.story_complete) return { label: 'STORY COMPLETE', detail: 'Your complete reflection is saved.' };
    if (session?.furthest_reached_seconds) return { label: 'CONTINUE WATCHING', detail: `Saved at ${formatTime(session.furthest_reached_seconds)}.` };
    return { label: 'READY TO WATCH', detail: 'Your spoiler-safe watch is ready.' };
  }
  if (activeProjectStatuses.includes(project.status)) return { label: 'PROCESSING', detail: project.progress.total_windows ? `${project.progress.completed_windows} of ${project.progress.total_windows} windows complete.` : 'Preparation is continuing in the background.' };
  if (project.status === 'FAILED_RETRIABLE') return { label: 'NEEDS RETRY', detail: 'The saved project can retry without creating a duplicate.' };
  if (project.status === 'FAILED') return { label: 'COULD NOT COMPLETE', detail: project.failure_message ?? 'No result was fabricated.' };
  return { label: 'NOT FINISHED', detail: 'Open this project to continue.' };
}

function Library() {
  const { user, loading } = useFirebaseUser();
  const [items, setItems] = useState<ProjectLibraryItem[]>();
  const [error, setError] = useState<string>();
  const [deleting, setDeleting] = useState<string>();
  useEffect(() => {
    if (user?.emailVerified) void api.listProjects().then(setItems).catch((caught) => setError(caught instanceof Error ? caught.message : 'Your videos could not be loaded.'));
  }, [user]);
  async function remove(item: ProjectLibraryItem) {
    const project = item.project;
    if (activeProjectStatuses.includes(project.status)) return;
    if (!window.confirm(`Delete "${project.title}" and its saved analysis? Your analysis allowance will not be restored.`)) return;
    setDeleting(project.id); setError(undefined);
    try {
      await api.deleteProject(project.id);
      sessionStorage.removeItem(sourceKey(project.id));
      setItems((current) => current?.filter((entry) => entry.project.id !== project.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The video could not be deleted.');
    } finally { setDeleting(undefined); }
  }
  if (loading) return <main className="app-shell"><Header quiet /><div className="center-message">Opening your video library...</div></main>;
  if (!user) return <main className="app-shell"><Header quiet /><SignInGate /></main>;
  if (!user.emailVerified) return <main className="app-shell"><Header quiet /><VerificationPanel user={user} /></main>;
  return <main className="app-shell"><Header quiet /><section className="library-page">
    <div className="library-heading"><div><p className="eyebrow blue">MY VIDEOS</p><h1>Your stories stay here.</h1><p>Analysis results and watch progress are saved to your account, so you can return from any device without paying to process the same video again.</p></div><button className="primary-action" onClick={() => go('/add')}>+ Analyze a video</button></div>
    {error && <p className="form-error" role="alert">{error}</p>}
    {items === undefined ? <div className="library-loading">Loading saved stories...</div> : items.length === 0 ? <section className="empty-library"><p className="eyebrow">YOUR LIBRARY IS QUIET</p><h2>Add your first story.</h2><p>Your analysis and viewing progress will be saved here.</p><button className="primary-action" onClick={() => go('/add')}>Analyze a video <b>→</b></button></section> : <div className="library-grid">{items.map((item) => {
      const project = item.project;
      const source = project.source;
      const videoId = source?.youtube_video_id ?? (source?.public_url ? youtubeId(source.public_url) : undefined);
      const state = libraryStatus(item);
      const isActive = activeProjectStatuses.includes(project.status);
      return <article className="library-card" key={project.id}><div className="library-thumb">{videoId ? <img src={`https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`} alt="" /> : <Mark />}<span>{source?.duration_seconds ? formatTime(source.duration_seconds) : 'VIDEO'}</span></div><div className="library-card-body"><p className="library-state">{state.label}</p><h2>{project.title}</h2><p>{state.detail}</p><small>Saved {new Date(project.updated_at).toLocaleDateString()}</small><div className="library-actions"><button className="primary-action compact" onClick={() => go(projectDestination(project, item.latest_session))}>{project.status === 'READY' || project.status === 'READY_NO_ECHO' ? item.latest_session?.story_complete ? 'View reflection' : item.latest_session?.furthest_reached_seconds ? 'Continue watching' : 'Watch story' : 'View progress'} <b>→</b></button><button className="text-link danger" onClick={() => void remove(item)} disabled={isActive || deleting === project.id} title={isActive ? 'Wait until processing finishes before deleting.' : undefined}>{deleting === project.id ? 'Deleting...' : 'Delete'}</button></div></div></article>;
    })}</div>}
    <p className="library-footnote">Deleting a saved video does not restore an analysis allowance because provider work has already been completed.</p>
  </section></main>;
}

function AddStory() {
  const { user, loading } = useFirebaseUser();
  const [account, setAccount] = useState<AccountStatus>();
  const [title, setTitle] = useState('');
  const [youtube, setYoutube] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  useEffect(() => {
    if (user?.emailVerified) void api.getAccount().then(setAccount).catch((caught) => setError(caught instanceof Error ? caught.message : 'Your allowance could not be loaded.'));
  }, [user]);
  const canSubmit = Boolean(title.trim() && youtube.trim() && account);
  if (loading) return <main className="app-shell"><Header quiet /><div className="center-message">Checking your account…</div></main>;
  if (!user) return <main className="app-shell"><Header quiet /><SignInGate /></main>;
  if (!user.emailVerified) return <main className="app-shell"><Header quiet /><VerificationPanel user={user} /></main>;
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit || busy) return;
    setBusy(true); setError(undefined);
    try {
      const existing = await api.findYoutubeProject(youtube);
      if (existing) {
        if (existing.project.status === 'SOURCE_PENDING') await api.startAnalysis(existing.project.id);
        go(projectDestination(existing.project, existing.latest_session));
        return;
      }
      if (!account?.analyses_remaining) throw new Error('Your analysis allowance is used. You can still reopen saved videos from My Videos.');
      const metadata = await inspectYoutube(youtube);
      if (metadata.duration > 360) throw new Error('Choose a public YouTube video no longer than 6 minutes.');
      const created = await api.createProject(title.trim());
      await api.setYoutubeSource(created.project_id, youtube, title.trim(), metadata.duration);
      await api.startAnalysis(created.project_id);
      go(`/processing/${created.project_id}`);
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'This story could not be added.'); }
    finally { setBusy(false); }
  }
  return <main className="app-shell"><Header quiet /><section className="source-page"><div className="source-intro"><p className="eyebrow blue">ANALYZE A STORY</p><h1>Give a new story<br />its first quiet room.</h1><p>Paste a public YouTube story up to six minutes. STILL follows it in bounded windows and may remain quiet when no reflection fits.</p><div className="source-notes"><span>○ Real Gemini audiovisual analysis—not a canned response.</span><span>○ At most one paid Gloo candidate per story.</span><span>○ Exact Scripture is retrieved from YouVersion only after acceptance.</span></div></div><form className="source-form" onSubmit={submit}>
    <div className="allowance-strip"><span>{account?.plan === 'ACCESS' ? 'ACCESS PASS' : 'FREE'}</span><strong>{account ? `${account.analyses_remaining} analysis${account.analyses_remaining === 1 ? '' : 'es'} available` : 'Loading allowance…'}</strong><button type="button" onClick={() => go('/account')}>Manage</button></div>
    <p className="eyebrow blue">NEW VIDEO</p>
    <label>Story title<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="A name you will recognize" maxLength={180} required /></label>
    <label>Public YouTube link<input value={youtube} onChange={(event) => setYoutube(event.target.value)} placeholder="https://www.youtube.com/watch?v=…" inputMode="url" required /><small>Public or unlisted, embeddable, with a fixed duration of 6:00 or less.</small></label>
    {clientConfig.appMode === 'production' && !firebaseConfigured && <p className="form-error" role="alert">Firebase Authentication is not configured. No fixture will be substituted.</p>}
    {account?.analyses_remaining === 0 && <p className="form-warning">Your current allowance is used. You can still reopen a saved result by entering the same link, or visit My Videos.</p>}
    {error && <p role="alert" className="form-error">{error}</p>}
    <button className="primary-action wide" disabled={!canSubmit || busy}>{busy ? 'Finding or queueing…' : 'Open or analyze this video'} <b>→</b></button>
    <p className="form-fineprint">By continuing, you confirm that the linked video may be processed. Provider work begins only after the server reserves your allowance.</p>
  </form></section></main>;
}

function stageCopy(project: Project) {
  const copy: Record<string, [string, string]> = {
    source_received: ['Story received.', 'Checking the source before anything is understood.'],
    preparing_media: ['Preparing the story.', 'Registering one reusable source for bounded analysis.'],
    understanding_story: ['Understanding the story.', 'Following it in order without looking ahead.'],
    grounding_reflection: ['Holding the right moments.', 'Only grounded reflections can pass this point.'],
    ready: ['Your story is ready.', 'Accepted Scripture moments unlock only after you reach them.'],
    failed: ['Analysis is unavailable.', 'Nothing has been invented or substituted.'],
  };
  return copy[project.progress.stage] ?? ['Preparing your story.', 'This project can continue in the background.'];
}

function Processing({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project>();
  const [error, setError] = useState<string>();
  const [retrying, setRetrying] = useState(false);
  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    const poll = async () => {
      try {
        const status = await api.getStatus(projectId);
        if (!active) return;
        setProject(status); setError(undefined);
        if (!['READY', 'READY_NO_ECHO', 'FAILED', 'FAILED_RETRIABLE', 'CANCELLED'].includes(status.status)) timer = window.setTimeout(() => void poll(), 3500);
      } catch (caught) {
        if (active) { setError(caught instanceof Error ? caught.message : 'Unable to read project status.'); timer = window.setTimeout(() => void poll(), 7000); }
      }
    };
    void poll();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [projectId]);
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
function sentenceCase(value: string) { return value ? value[0].toUpperCase() + value.slice(1) : value; }

function Watch({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project>();
  const [session, setSession] = useState<ViewingSession>();
  const [echoes, setEchoes] = useState<Echo[]>([]);
  const [echoesLoaded, setEchoesLoaded] = useState(false);
  const [expandedEchoId, setExpandedEchoId] = useState<string>();
  const [playerState, setPlayerState] = useState<'idle' | 'playing' | 'paused' | 'ended'>('idle');
  const [time, setTime] = useState(0);
  const [resumeAt, setResumeAt] = useState(0);
  const [error, setError] = useState<string>();
  const videoRef = useState(() => ({ current: null as HTMLVideoElement | null }))[0];
  const youtubeRef = useState(() => ({ current: null as HTMLDivElement | null }))[0];
  const adapterRef = useState(() => ({ current: undefined as PlaybackAdapter | undefined }))[0];
  const trackerRef = useState(() => new WatchedRangeTracker())[0];
  const syncState = useState(() => ({ inFlight: false, lastBucket: -1, endedPending: false }))[0];
  const source = project?.source;
  const sourceUrl = sessionStorage.getItem(sourceKey(projectId));
  const sessionId = session?.id;

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [loaded, started] = await Promise.all([api.getProject(projectId), api.resumeSession(projectId)]);
        if (active) {
          setProject(loaded.project);
          trackerRef.restore(started.watched_ranges);
          const savedPosition = started.furthest_reached_seconds || started.contiguous_frontier_seconds;
          setResumeAt(savedPosition);
          setTime(savedPosition);
          setSession(started);
        }
      } catch (caught) { if (active) setError(caught instanceof Error ? caught.message : 'This watch session could not start.'); }
    })();
    return () => { active = false; };
  }, [projectId, trackerRef]);

  useEffect(() => {
    if (!source || !sessionId) return;
    let disposed = false;
    const setup = async () => {
      try {
        let adapter: PlaybackAdapter;
        if (source.kind === 'youtube' && source.public_url && youtubeRef.current) {
          adapter = new YouTubePlaybackAdapter(youtubeRef.current);
          await adapter.load(youtubeId(source.public_url) ?? '');
        } else if (source.kind === 'upload' && sourceUrl && videoRef.current) {
          adapter = new Html5PlaybackAdapter(videoRef.current);
          await adapter.load(sourceUrl);
        } else {
          setError('Playback requires the original authorized source. No substitute media is shown.');
          return;
        }
        if (disposed) { adapter.destroy(); return; }
        adapterRef.current = adapter;
        if (resumeAt > 1 && source.duration_seconds) {
          adapter.seek(Math.min(resumeAt, Math.max(0, source.duration_seconds - 2)));
        }
        const sync = async (endedNaturally = false) => {
          if (endedNaturally) syncState.endedPending = true;
          if (!sessionId || !source.duration_seconds || syncState.inFlight) return;
          syncState.inFlight = true;
          const saveNaturalEnd = syncState.endedPending;
          syncState.endedPending = false;
          try {
            const next = await api.updateSession(projectId, sessionId, { ranges: trackerRef.snapshot(), duration_seconds: source.duration_seconds, current_position_seconds: adapter.getCurrentTime(), ended_naturally: saveNaturalEnd });
            if (!disposed) setSession(next);
          } catch (caught) { if (!disposed) setError(caught instanceof Error ? caught.message : 'Watch progress could not be saved.'); }
          finally {
            syncState.inFlight = false;
            if (syncState.endedPending && !disposed) void sync();
          }
        };
        const unsubscribe = [
          adapter.onTimeUpdate((value) => {
            trackerRef.sample(value, adapter.getPlaybackRate());
            setTime(value);
            const bucket = Math.floor(value / 5);
            if (bucket > syncState.lastBucket) {
              syncState.lastBucket = bucket;
              void sync();
            }
          }),
          adapter.onSeek(() => trackerRef.markSeeking()),
          adapter.onStateChange((state) => { trackerRef.setPlaying(state === 'playing'); setPlayerState(state); if (state === 'paused') void sync(); }),
          adapter.onEnded(() => void sync(true)),
        ];
        return () => unsubscribe.forEach((off) => off());
      } catch (caught) { if (!disposed) setError(caught instanceof Error ? caught.message : 'Playback could not be loaded.'); }
    };
    let teardown: (() => void) | undefined;
    void setup().then((result) => { teardown = result; });
    return () => { disposed = true; teardown?.(); adapterRef.current?.destroy(); adapterRef.current = undefined; };
  }, [adapterRef, projectId, resumeAt, sessionId, source, sourceUrl, syncState, trackerRef, videoRef, youtubeRef]);

  useEffect(() => {
    if (!sessionId) return;
    let active = true;
    void api.getEchoes(projectId, sessionId).then((next) => { if (active) { setEchoes(next); setEchoesLoaded(true); } }).catch((caught) => { if (active) { setEchoesLoaded(true); setError(caught instanceof Error ? caught.message : 'Reflections are unavailable.'); } });
    return () => { active = false; };
  }, [projectId, session?.furthest_reached_seconds, sessionId]);
  if (!project || !source) return <main className="app-shell"><Header quiet /><div className="center-message">Opening the quiet room…</div>{error && <p className="form-error reflect-error">{error}</p>}</main>;
  return <main className="watch-shell"><Header quiet /><section className="watch-header"><p className="eyebrow blue">WATCH & REFLECT</p><h1>{project.title}</h1><span>{formatTime(time)} / {formatTime(source.duration_seconds ?? 0)}</span></section><section className="watch-stage"><div className="video-frame">{source.kind === 'youtube' ? <div ref={(node) => { youtubeRef.current = node; }} className="youtube-frame" title="YouTube story" /> : <video ref={(node) => { videoRef.current = node; }} controls playsInline preload="metadata" aria-label={`Video: ${project.title}`} />}<div className="video-corner top">STILL / TIMED TO VIDEO</div><div className="video-corner bottom">{playerState === 'playing' ? 'PLAYING' : 'QUIETLY WAITING'}</div></div><aside className="watch-aside"><p className="eyebrow">FURTHEST MOMENT REACHED</p><strong>{formatTime(session?.furthest_reached_seconds ?? 0)}</strong><span>Reflections through this video timestamp can appear below—even after you scrub forward.</span><button className="secondary-action" onClick={() => void adapterRef.current?.play()}>Continue story <b>→</b></button></aside></section><section className="timed-reflections" aria-live="polite"><div className="timed-reflection-heading"><div><p className="eyebrow blue">SCRIPTURE AT THE RIGHT MOMENT</p><h2>Reflections unlock as you watch.</h2><p>Play or scrub to a moment, then open any unlocked reflection when you want to go deeper.</p></div><strong>{!echoesLoaded ? 'Checking moments' : echoes.length ? `${echoes.length} unlocked` : 'Listening with you'}</strong></div>{!echoesLoaded ? <p className="empty-reflection">Checking which grounded moments are available at your saved video position…</p> : echoes.length ? <div className="timed-echo-list">{echoes.map((echo) => { const expanded = expandedEchoId === echo.id; return <article className={`timed-echo ${expanded ? 'expanded' : ''}`} key={echo.id}><button className="timed-echo-summary" onClick={() => { adapterRef.current?.pause(); setExpandedEchoId(expanded ? undefined : echo.id); }} aria-expanded={expanded}><span><small>UNLOCKED AT {formatTime(echo.knowledge_cutoff_seconds)}</small><b>{sentenceCase(echo.tension)}</b>{echo.scripture_reference && <em>{echo.scripture_reference} · {echo.bible_version}</em>}</span><i>{expanded ? 'Close' : 'Open reflection'} →</i></button>{expanded && <div className="timed-echo-detail"><p className="scene-context">{echo.scene_context}</p>{echo.exact_scripture_text && <figure><blockquote>{echo.exact_scripture_text}</blockquote><figcaption>{echo.scripture_reference} {echo.bible_version ? `· ${echo.bible_version}` : ''}</figcaption><small>{echo.copyright_attribution}</small></figure>}{echo.connection_explanation && <div className="why-it-connects"><span>WHY IT CONNECTS</span><p>{echo.connection_explanation}</p></div>}</div>}</article>; })}</div> : <p className="empty-reflection">{project.status === 'READY_NO_ECHO' ? 'This analysis completed without a proportionate Scripture connection. STILL will not force one.' : 'No reflection is unlocked yet. A grounded Scripture moment will appear here automatically when you reach it.'}</p>}</section>{session?.story_complete && <section className="story-complete"><p className="eyebrow blue">STORY COMPLETE</p><h2>The whole story has room to breathe now.</h2><p>You watched it through. Review every unlocked reflection with the complete story in view.</p><button className="primary-action" onClick={() => go(`/reflect/${projectId}`)}>Review all reflections <b>→</b></button></section>}{error && <p className="watch-error" role="alert">{error}</p>}</main>;
}

function Reflect({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project>();
  const [echoes, setEchoes] = useState<Echo[]>();
  const [error, setError] = useState<string>();
  useEffect(() => {
    void (async () => {
      try {
        const session = await api.resumeSession(projectId);
        const [loaded, reflection] = await Promise.all([api.getProject(projectId), api.getStoryReflection(projectId, session.id)]);
        setProject(loaded.project); setEchoes(reflection);
      } catch (caught) { setError(caught instanceof Error ? caught.message : 'Full reflection is not available yet.'); }
    })();
  }, [projectId]);
  return <main className="reflect-shell"><Header quiet /><section className="reflect-intro"><p className="eyebrow blue">AFTER THE STORY</p><h1>{project?.title ?? 'Reflection'}</h1><p>These moments are grounded in the complete story you watched. Scripture is shown only when retrieved with its version and attribution.</p></section>{error && <p className="form-error reflect-error" role="alert">{error}</p>}{echoes?.length === 0 && <section className="no-echo"><p className="eyebrow">STILL REMAINED QUIET</p><h2>No Scripture Echo was forced into this story.</h2><p>That is a complete result, not a missing one.</p><button className="secondary-action" onClick={() => go(`/watch/${projectId}`)}>Return to story</button></section>}<section className="echo-list">{echoes?.map((echo, index) => <article className="full-echo" key={echo.id}><div className="echo-number">0{index + 1}</div><div><p className="timestamp">A moment at {formatTime(echo.knowledge_cutoff_seconds)}</p><h2>{sentenceCase(echo.tension)}</h2><p className="scene-context">{echo.scene_context}</p>{echo.exact_scripture_text && <figure><blockquote>{echo.exact_scripture_text}</blockquote><figcaption>{echo.scripture_reference} {echo.bible_version ? `· ${echo.bible_version}` : ''}</figcaption><small>{echo.copyright_attribution}</small></figure>}{echo.connection_explanation && <p className="connection">{echo.connection_explanation}</p>}</div></article>)}</section></main>;
}

export default function App() {
  const route = useRoute();
  if (route.page === 'add') return <AddStory />;
  if (route.page === 'auth') return <AuthPage />;
  if (route.page === 'plans') return <Plans />;
  if (route.page === 'account') return <AccountPage />;
  if (route.page === 'library') return <Library />;
  if (route.page === 'processing' && route.projectId) return <ProtectedRoute><Processing key={route.projectId} projectId={route.projectId} /></ProtectedRoute>;
  if (route.page === 'watch' && route.projectId) return <ProtectedRoute><Watch key={route.projectId} projectId={route.projectId} /></ProtectedRoute>;
  if (route.page === 'reflect' && route.projectId) return <ProtectedRoute><Reflect key={route.projectId} projectId={route.projectId} /></ProtectedRoute>;
  return <Landing />;
}

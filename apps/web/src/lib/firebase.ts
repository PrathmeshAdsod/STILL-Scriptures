import { getApp, getApps, initializeApp } from 'firebase/app';
import { GoogleAuthProvider, getAuth, onAuthStateChanged, signInAnonymously, signInWithPopup, type User } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getDownloadURL, getStorage, ref, uploadBytesResumable } from 'firebase/storage';
import { clientConfig, firebaseConfigured } from './config';

const firebaseApp = firebaseConfigured
  ? (getApps().length ? getApp() : initializeApp(clientConfig.firebase))
  : undefined;

export const firebaseAuth = firebaseApp ? getAuth(firebaseApp) : undefined;
export const firebaseDb = firebaseApp ? getFirestore(firebaseApp) : undefined;
export const firebaseStorage = firebaseApp ? getStorage(firebaseApp) : undefined;

export async function getIdToken(): Promise<string | undefined> {
  if (!firebaseAuth) return undefined;
  if (!firebaseAuth.currentUser && (clientConfig.appMode === 'development' || clientConfig.publicShowcase)) await signInAnonymously(firebaseAuth);
  return firebaseAuth.currentUser?.getIdToken();
}

export function observeFirebaseUser(listener: (user: User | null) => void): () => void {
  if (!firebaseAuth) {
    listener(null);
    return () => undefined;
  }
  return onAuthStateChanged(firebaseAuth, listener);
}

export async function signInToStill(): Promise<void> {
  if (!firebaseAuth) throw new Error('Firebase Authentication is not configured in this environment.');
  if (firebaseAuth.currentUser) return;
  if (clientConfig.appMode === 'development' || clientConfig.publicShowcase) {
    await signInAnonymously(firebaseAuth);
    return;
  }
  await signInWithPopup(firebaseAuth, new GoogleAuthProvider());
}

export async function signInJudgeAnonymously(): Promise<void> {
  if (!firebaseAuth) throw new Error('Firebase Authentication is not configured for this demo.');
  if (!firebaseAuth.currentUser) await signInAnonymously(firebaseAuth);
}

export function activeFirebaseUid(): string | undefined {
  return firebaseAuth?.currentUser?.uid;
}

export async function uploadVideo(
  file: File,
  projectId: string,
  onProgress: (progress: number) => void,
): Promise<{ storagePath: string; playbackUrl: string }> {
  if (!firebaseStorage || !clientConfig.firebase.storageBucket) {
    throw new Error('Firebase Storage is not configured. This upload cannot be completed yet.');
  }
  const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
  const objectRef = ref(firebaseStorage, `projects/${projectId}/sources/${crypto.randomUUID()}-${safeName}`);
  const task = uploadBytesResumable(objectRef, file, { contentType: file.type });
  await new Promise<void>((resolve, reject) => {
    task.on('state_changed', (snapshot) => onProgress(snapshot.bytesTransferred / snapshot.totalBytes), reject, resolve);
  });
  return { storagePath: `gs://${clientConfig.firebase.storageBucket}/${objectRef.fullPath}`, playbackUrl: await getDownloadURL(objectRef) };
}

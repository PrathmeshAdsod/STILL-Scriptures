import { getApp, getApps, initializeApp } from 'firebase/app';
import {
  createUserWithEmailAndPassword,
  getAuth,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from 'firebase/auth';
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
  return firebaseAuth.currentUser?.getIdToken();
}

export function observeFirebaseUser(listener: (user: User | null) => void): () => void {
  if (!firebaseAuth) {
    listener(null);
    return () => undefined;
  }
  return onAuthStateChanged(firebaseAuth, listener);
}

export async function createStillAccount(email: string, password: string): Promise<User> {
  if (!firebaseAuth) throw new Error('Firebase Authentication is not configured in this environment.');
  const credential = await createUserWithEmailAndPassword(firebaseAuth, email.trim(), password);
  await sendEmailVerification(credential.user);
  return credential.user;
}

export async function signInToStill(email: string, password: string): Promise<User> {
  if (!firebaseAuth) throw new Error('Firebase Authentication is not configured in this environment.');
  return (await signInWithEmailAndPassword(firebaseAuth, email.trim(), password)).user;
}

export async function signOutOfStill(): Promise<void> {
  if (firebaseAuth) await signOut(firebaseAuth);
}

export async function sendStillPasswordReset(email: string): Promise<void> {
  if (!firebaseAuth) throw new Error('Firebase Authentication is not configured in this environment.');
  await sendPasswordResetEmail(firebaseAuth, email.trim());
}

export async function resendStillVerification(): Promise<void> {
  if (!firebaseAuth?.currentUser) throw new Error('Sign in before requesting another verification email.');
  await sendEmailVerification(firebaseAuth.currentUser);
}

export async function refreshStillUser(): Promise<User | null> {
  if (!firebaseAuth?.currentUser) return null;
  await firebaseAuth.currentUser.reload();
  await firebaseAuth.currentUser.getIdToken(true);
  return firebaseAuth.currentUser;
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

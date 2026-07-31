const appMode = import.meta.env.VITE_APP_MODE ?? 'development';
const fixturesEnabled = import.meta.env.VITE_USE_PROVIDER_FIXTURES === 'true';

if (appMode === 'production' && fixturesEnabled) {
  throw new Error('Production refuses to start with VITE_USE_PROVIDER_FIXTURES=true.');
}

export const clientConfig = {
  appMode,
  fixturesEnabled,
  githubUrl: import.meta.env.VITE_GITHUB_URL ?? 'https://github.com/PrathmeshAdsod/STILL-Scriptures',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api',
  firebase: {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
  },
};

export const firebaseConfigured = Object.values(clientConfig.firebase).every(Boolean);

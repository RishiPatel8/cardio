import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";
import { getMessaging, isSupported as isMessagingSupported } from "firebase/messaging";
import { getAnalytics, isSupported as isAnalyticsSupported } from "firebase/analytics";
import { getRemoteConfig } from "firebase/remote-config";
import { initializeAppCheck, ReCaptchaEnterpriseProvider, CustomProvider } from "firebase/app-check";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyA-mock-key-for-transpile-purposes",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "cardioguard-ai.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "cardioguard-ai",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "cardioguard-ai.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1234567890",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1234567890:web:abcdef123456",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-MOCKMEASURE",
};

// Initialize Firebase App
export const app = initializeApp(firebaseConfig);

// Initialize Firebase Auth
export const auth = getAuth(app);

// Initialize Cloud Firestore
export const db = getFirestore(app);

// Initialize Cloud Storage
export const storage = getStorage(app);

// Initialize Remote Config
export const remoteConfig = getRemoteConfig(app);
if (remoteConfig && remoteConfig.settings) {
  remoteConfig.settings.minimumFetchIntervalMillis = 3600000; // 1 hour
}
if (remoteConfig) {
  remoteConfig.defaultConfig = {
    ai_threshold: 0.65,
    alert_interval_seconds: 60,
  };
}

// Conditional integrations for Messaging and Analytics
export let messaging: any = null;
isMessagingSupported().then((supported) => {
  if (supported) {
    messaging = getMessaging(app);
  }
});

export let analytics: any = null;
isAnalyticsSupported().then((supported) => {
  if (supported) {
    analytics = getAnalytics(app);
  }
});

// App Check mappings
export let appCheck: any = null;
if (typeof window !== "undefined") {
  // TODO: Re-enable Firebase App Check in production mode by setting VITE_APP_CHECK_ENABLED=true in .env
  const appCheckEnabled = import.meta.env.VITE_APP_CHECK_ENABLED !== "false";
  if (appCheckEnabled) {
    try {
      const isDev = import.meta.env.DEV || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      let provider;
      
      if (isDev && !import.meta.env.VITE_APPCHECK_DEBUG_TOKEN) {
        provider = new CustomProvider({
          getToken: async () => ({
            token: "mock_app_check_token_local",
            expireTimeMillis: Date.now() + 3600 * 1000,
          }),
        });
      } else {
        if (isDev && import.meta.env.VITE_APPCHECK_DEBUG_TOKEN) {
          (window as any).FIREBASE_APPCHECK_DEBUG_TOKEN = import.meta.env.VITE_APPCHECK_DEBUG_TOKEN;
        }
        provider = new ReCaptchaEnterpriseProvider(import.meta.env.VITE_RECAPTCHA_SITE_KEY || "6LdMockSiteKeyForCardioGuardAppCheck123");
      }

      appCheck = initializeAppCheck(app, {
        provider,
        isTokenAutoRefreshEnabled: true,
      });
    } catch {
      // Gracefully handle app check initializations in local dev setups
    }
  } else {
    console.log("[Firebase App Check] Disabled via VITE_APP_CHECK_ENABLED=false config switch.");
  }
}

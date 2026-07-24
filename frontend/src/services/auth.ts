import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onIdTokenChanged,
} from "firebase/auth";
import type { User as FirebaseUser } from "firebase/auth";
import { auth } from "./firebase";
import { logAnalyticsEvent } from "./analytics";

const googleProvider = new GoogleAuthProvider();

export const loginWithEmail = async (email: string, pass: string) => {
  const creds = await signInWithEmailAndPassword(auth, email, pass);
  logAnalyticsEvent("login_completed", { method: "email", user_id: creds.user.uid });
  return creds.user;
};

export const registerWithEmail = async (email: string, pass: string) => {
  const creds = await createUserWithEmailAndPassword(auth, email, pass);
  logAnalyticsEvent("signup_completed", { method: "email", user_id: creds.user.uid });
  return creds.user;
};

export const loginWithGoogle = async () => {
  const isCapacitor = (window as any).Capacitor !== undefined;
  
  if (isCapacitor) {
    try {
      await signInWithRedirect(auth, googleProvider);
    } catch (e) {
      console.warn("signInWithRedirect failed, attempting popup", e);
      const creds = await signInWithPopup(auth, googleProvider);
      return creds.user;
    }
  } else {
    try {
      const creds = await signInWithPopup(auth, googleProvider);
      logAnalyticsEvent("login_completed", { method: "google", user_id: creds.user.uid });
      return creds.user;
    } catch (popupError) {
      console.warn("signInWithPopup failed, falling back to redirect", popupError);
      await signInWithRedirect(auth, googleProvider);
    }
  }
};

export const handleRedirectResult = async () => {
  try {
    const result = await getRedirectResult(auth);
    if (result) {
      logAnalyticsEvent("login_completed", { method: "google_redirect", user_id: result.user.uid });
      return result.user;
    }
  } catch (error) {
    console.error("Firebase redirect result handling failed", error);
  }
  return null;
};

export const signOutUser = async () => {
  logAnalyticsEvent("logout_completed");
  await firebaseSignOut(auth);
};

export const getUserToken = async (forceRefresh = false): Promise<string | null> => {
  const user = auth.currentUser;
  if (!user) return null;
  return await user.getIdToken(forceRefresh);
};

export const subscribeToAuthChanges = (callback: (user: FirebaseUser | null) => void) => {
  return onIdTokenChanged(auth, callback);
};

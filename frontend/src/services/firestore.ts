import { doc, setDoc, getDoc, collection, addDoc } from "firebase/firestore";
import { db } from "./firebase";
import { logAnalyticsEvent } from "./analytics";

export const syncUserProfile = async (userId: string, profileData: Record<string, any>) => {
  const userRef = doc(db, "users", userId);
  await setDoc(userRef, profileData, { merge: true });
  logAnalyticsEvent("user_profile_synced", { user_id: userId });
};

export const fetchUserProfile = async (userId: string) => {
  const userRef = doc(db, "users", userId);
  const snap = await getDoc(userRef);
  return snap.exists() ? snap.data() : null;
};

export const syncTelemetrySummary = async (userId: string, data: Record<string, any>) => {
  const telemetryCollection = collection(db, "users", userId, "telemetry");
  const docRef = await addDoc(telemetryCollection, {
    ...data,
    timestamp: new Date().toISOString()
  });
  logAnalyticsEvent("telemetry_summary_synced", { user_id: userId, doc_id: docRef.id });
  return docRef.id;
};

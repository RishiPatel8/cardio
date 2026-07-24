import { logEvent } from "firebase/analytics";
import { analytics } from "./firebase";

export const logAnalyticsEvent = (eventName: string, params?: Record<string, any>) => {
  try {
    if (analytics) {
      logEvent(analytics, eventName, params);
      console.log(`[Firebase Analytics] Event logged: ${eventName}`, params);
    } else {
      console.log(`[Firebase Analytics Mock] Event logged: ${eventName}`, params);
    }
  } catch (e) {
    console.error("Failed to log analytics event", e);
  }
};

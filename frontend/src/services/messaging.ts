import { getToken, onMessage } from "firebase/messaging";
import { messaging } from "./firebase";
import { logAnalyticsEvent } from "./analytics";

export const getFCMToken = async (vapidKey: string): Promise<string | null> => {
  try {
    if (!messaging) return null;
    const token = await getToken(messaging, { vapidKey });
    if (token) {
      logAnalyticsEvent("fcm_token_registered");
      return token;
    }
    return null;
  } catch (e) {
    console.error("FCM registration failed", e);
    return null;
  }
};

export const onIncomingMessage = (callback: (payload: any) => void) => {
  if (!messaging) return () => {};
  return onMessage(messaging, (payload) => {
    logAnalyticsEvent("fcm_message_received", { message_id: payload.messageId });
    callback(payload);
  });
};

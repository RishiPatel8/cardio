import { getToken } from "firebase/app-check";
import { appCheck } from "./firebase";

export const getAppCheckToken = async (): Promise<string | null> => {
  try {
    if (!appCheck) return null;
    const tokenResult = await getToken(appCheck, false);
    return tokenResult.token;
  } catch (error) {
    console.warn("App Check token fetching failed.", error);
    return null;
  }
};

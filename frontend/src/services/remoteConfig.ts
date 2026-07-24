import { fetchAndActivate, getValue } from "firebase/remote-config";
import { remoteConfig } from "./firebase";

export const fetchAIThresholdConfig = async (): Promise<number> => {
  try {
    await fetchAndActivate(remoteConfig);
    const val = getValue(remoteConfig, "ai_threshold");
    return val.asNumber();
  } catch {
    console.warn("Failed to fetch remote config for ai_threshold. Using default value.");
    return 0.65;
  }
};

export const fetchAlertIntervalConfig = async (): Promise<number> => {
  try {
    await fetchAndActivate(remoteConfig);
    const val = getValue(remoteConfig, "alert_interval_seconds");
    return val.asNumber();
  } catch {
    console.warn("Failed to fetch remote config for alert_interval_seconds. Using default value.");
    return 60;
  }
};

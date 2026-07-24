import { describe, it, expect, vi } from "vitest";

// Mock Firebase Remote Config calls
vi.mock("firebase/remote-config", () => ({
  getRemoteConfig: vi.fn(() => ({})),
  fetchAndActivate: vi.fn(() => Promise.resolve(true)),
  getValue: vi.fn((_, key) => ({
    asNumber: () => {
      if (key === "ai_threshold") return 0.75;
      if (key === "alert_interval_seconds") return 45;
      return 0.0;
    }
  })),
}));

vi.mock("../firebase", () => ({
  remoteConfig: {}
}));

import { fetchAIThresholdConfig, fetchAlertIntervalConfig } from "../remoteConfig";

describe("Firebase Remote Config Service Tests", () => {
  it("should successfully retrieve the custom AI threshold configuration", async () => {
    const threshold = await fetchAIThresholdConfig();
    expect(threshold).toBe(0.75);
  });

  it("should successfully retrieve the custom alert interval configuration", async () => {
    const interval = await fetchAlertIntervalConfig();
    expect(interval).toBe(45);
  });
});

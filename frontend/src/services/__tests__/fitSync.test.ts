import { describe, it, expect } from "vitest";
import { auditFitData, verifyTelemetryConsistency } from "../fitSync";

describe("Google Fit / Health Connect Sync & Audit Tests", () => {
  it("should filter out duplicate records by timestamp and calculate correct average BPM", () => {
    const rawData = [
      { time: "2026-07-24T12:00:00Z", bpm: 70 },
      { time: "2026-07-24T12:05:00Z", bpm: 80 },
      { time: "2026-07-24T12:00:00Z", bpm: 90 }, // Duplicate timestamp (filtered out)
      { time: "2026-07-24T12:10:00Z", bpm: 90 }
    ];

    const result = auditFitData(rawData);
    
    // Deduplication should ensure only 70, 80, and 90 are processed
    // Average: (70 + 80 + 90) / 3 = 80
    expect(result.avgBpm).toBe(80);
    expect(result.steps).toBe(6200);
  });

  it("should fallback to default wellness values if no input data is provided", () => {
    const result = auditFitData([]);
    expect(result.avgBpm).toBe(72);
    expect(result.steps).toBe(6200);
    expect(result.calories).toBe(320);
    expect(result.sleepMinutes).toBe(432);
  });

  it("should validate telemetry consistency within acceptable delta thresholds", () => {
    const frontend = { avgBpm: 75, steps: 6000 };
    const backend = { avgBpm: 76, steps: 6050 };

    const consistent = verifyTelemetryConsistency(frontend, backend);
    expect(consistent).toBe(true);
  });

  it("should report inconsistency if average heart rate difference exceeds limits", () => {
    const frontend = { avgBpm: 75, steps: 6000 };
    const backend = { avgBpm: 78, steps: 6050 }; // Difference = 3 (> 2 bpm limit)

    const consistent = verifyTelemetryConsistency(frontend, backend);
    expect(consistent).toBe(false);
  });

  it("should report inconsistency if total steps count difference exceeds limits", () => {
    const frontend = { avgBpm: 75, steps: 6000 };
    const backend = { avgBpm: 76, steps: 6200 }; // Difference = 200 (> 100 steps limit)

    const consistent = verifyTelemetryConsistency(frontend, backend);
    expect(consistent).toBe(false);
  });
});

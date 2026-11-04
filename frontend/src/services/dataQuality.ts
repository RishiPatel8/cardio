// Vitals & Sensor Data Quality Validation Engine

export interface TelemetryPacket {
  avg_bpm: number;
  sdrr_ms: number;
  rmssd_ms: number;
  steps_count: number;
  calories_burned: number;
  sleep_minutes: number;
  spo2: number;
  systolic_bp: number;
  diastolic_bp: number;
}

export interface QualityValidationResult {
  score: number;       // 0 to 100%
  issues: string[];    // Descriptions of warning thresholds violated
  passed: boolean;     // True if score >= 80% (acceptable for AI inference)
}

export const validateTelemetryPacket = (data: Partial<TelemetryPacket>): QualityValidationResult => {
  const issues: string[] = [];
  let totalChecks = 9;
  let passedChecks = 9;

  const checkRange = (val: number | undefined, min: number, max: number, name: string) => {
    if (val === undefined || val === null || isNaN(val)) {
      issues.push(`Missing biometric sensor index: ${name}`);
      passedChecks--;
      return;
    }
    if (val <= 0) {
      issues.push(`Empty value registered on: ${name}`);
      passedChecks--;
      return;
    }
    if (val < min || val > max) {
      issues.push(`Physiologically out-of-bounds metrics: ${name} (${val}). Expected range: ${min}-${max}`);
      passedChecks--;
    }
  };

  // 1. Avg BPM Check
  checkRange(data.avg_bpm, 30, 220, "Heart Rate (BPM)");

  // 2. SDRR Check
  checkRange(data.sdrr_ms, 5, 500, "SDRR (HRV)");

  // 3. RMSSD Check
  checkRange(data.rmssd_ms, 5, 500, "RMSSD (HRV)");

  // 4. SpO2 Check
  checkRange(data.spo2, 80, 100, "Oxygen Saturation (SpO₂)");

  // 5. Systolic BP Check
  checkRange(data.systolic_bp, 70, 240, "Systolic Blood Pressure");

  // 6. Diastolic BP Check
  checkRange(data.diastolic_bp, 40, 140, "Diastolic Blood Pressure");

  // 7. Sleep Check
  if (data.sleep_minutes !== undefined && data.sleep_minutes !== null) {
    if (data.sleep_minutes < 0 || data.sleep_minutes > 1440) {
      issues.push("Impossible rest parameters logged (Sleep > 24 hours)");
      passedChecks--;
    }
  } else {
    issues.push("Missing sleep duration logs");
    passedChecks--;
  }

  // 8. Steps Check
  if (data.steps_count !== undefined && data.steps_count !== null) {
    if (data.steps_count < 0 || data.steps_count > 100000) {
      issues.push("Improbable active steps count (> 100,000 steps)");
      passedChecks--;
    }
  } else {
    issues.push("Missing steps count metrics");
    passedChecks--;
  }

  // 9. Calories Check
  if (data.calories_burned !== undefined && data.calories_burned !== null) {
    if (data.calories_burned < 0 || data.calories_burned > 10000) {
      issues.push("Improbable caloric expenditure metrics (> 10,000 kcal)");
      passedChecks--;
    }
  } else {
    issues.push("Missing active caloric expenditure logs");
    passedChecks--;
  }

  const score = Math.max(0, Math.round((passedChecks / totalChecks) * 100));
  const passed = score >= 80;

  return {
    score,
    issues,
    passed
  };
};

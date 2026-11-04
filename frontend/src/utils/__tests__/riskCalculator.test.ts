import { describe, it, expect } from 'vitest';
import { calculateCardiovascularRisk } from '../riskCalculator';

describe('calculateCardiovascularRisk', () => {
  const defaultProfile = {
    hypertension: false,
    smoking: false,
  };

  it('should fallback to 74% (High AF Risk) when no probability vector is provided but isAF is true', () => {
    const { riskString, isAnomaly } = calculateCardiovascularRisk(undefined, true, defaultProfile);
    expect(riskString).toBe('74% (High AF Risk)');
    expect(isAnomaly).toBe(true);
  });

  it('should fallback to 4.8% (Optimal Risk) when no probability vector is provided and profile is healthy', () => {
    const { riskString, isAnomaly } = calculateCardiovascularRisk(undefined, false, defaultProfile);
    expect(riskString).toBe('4.8% (Optimal Risk)');
    expect(isAnomaly).toBe(false);
  });

  it('should fallback to 14.2% (Moderate Risk) when no probability vector is provided and profile has hypertension', () => {
    const { riskString, isAnomaly } = calculateCardiovascularRisk(undefined, false, { hypertension: true });
    expect(riskString).toBe('14.2% (Moderate Risk)');
    expect(isAnomaly).toBe(false); // isAnomaly depends only on isAF in fallback
  });

  it('should display the highest probability class dynamically (Conduction Block)', () => {
    const probabilityVector = [0.009, 0.032, 0.5308897, 0.4276515];
    const { riskString, isAnomaly } = calculateCardiovascularRisk(probabilityVector, false, defaultProfile);
    expect(riskString).toBe('53.1% (High Conduction Block Risk)');
    expect(isAnomaly).toBe(true);
  });

  it('should display the highest probability class dynamically (AFIB)', () => {
    const probabilityVector = [0.10, 0.80, 0.05, 0.05];
    const { riskString, isAnomaly } = calculateCardiovascularRisk(probabilityVector, true, defaultProfile);
    expect(riskString).toBe('80.0% (High AFIB Risk)');
    expect(isAnomaly).toBe(true);
  });

  it('should display the highest probability class dynamically (Other Arrhythmia)', () => {
    const probabilityVector = [0.10, 0.10, 0.15, 0.65];
    const { riskString, isAnomaly } = calculateCardiovascularRisk(probabilityVector, false, defaultProfile);
    expect(riskString).toBe('65.0% (High Other Arrhythmia Risk)');
    expect(isAnomaly).toBe(true);
  });

  it('should display appropriate low-risk/normal interpretation when Normal Sinus Rhythm is highest', () => {
    const probabilityVector = [0.90, 0.02, 0.03, 0.05];
    const { riskString, isAnomaly } = calculateCardiovascularRisk(probabilityVector, false, defaultProfile);
    expect(riskString).toBe('90.0% (Optimal / Normal Rhythm)');
    expect(isAnomaly).toBe(false);
  });
});

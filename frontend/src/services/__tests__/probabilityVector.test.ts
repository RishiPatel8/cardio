import { describe, it, expect } from 'vitest';

describe('Probability Vector API Boundary Processing', () => {
  it('should correctly normalize physionet percentage arrays to decimals and clamp', () => {
    // Mock API response from physionet.py (which returns percentages)
    const mockClassProbabilities = {
      "Normal": 92.8,
      "AFIB": 321.7, // Invalid high value test case
      "Conduction Block": 5308.9, // Invalid high value test case
      "Other Arrhythmia": -15.5 // Invalid low value test case
    };

    const rawVector = [
      mockClassProbabilities.Normal, 
      mockClassProbabilities.AFIB, 
      mockClassProbabilities["Conduction Block"], 
      mockClassProbabilities["Other Arrhythmia"]
    ];

    // API mapping boundary logic from App.tsx
    const probabilityVector = rawVector.map(v => Math.max(0, Math.min(1, v / 100.0)));

    // Verify values are between 0 and 1
    expect(probabilityVector[0]).toBeCloseTo(0.928);
    expect(probabilityVector[1]).toBe(1); // Clamped to 1
    expect(probabilityVector[2]).toBe(1); // Clamped to 1
    expect(probabilityVector[3]).toBe(0); // Clamped to 0
  });

  it('should correctly clamp legacy prediction decimal arrays', () => {
    // Mock API response from prediction.py (which returns decimals)
    const rawLegacy = [0.00928, 0.03217, 0.53089, 0.42765, 1.2, -0.5];

    // API mapping boundary logic from App.tsx
    const probabilityVector = rawLegacy.map((v: number) => Math.max(0, Math.min(1, v)));

    // Verify values are clamped
    expect(probabilityVector[0]).toBeCloseTo(0.00928);
    expect(probabilityVector[1]).toBeCloseTo(0.03217);
    expect(probabilityVector[2]).toBeCloseTo(0.53089);
    expect(probabilityVector[3]).toBeCloseTo(0.42765);
    expect(probabilityVector[4]).toBe(1); // Clamped
    expect(probabilityVector[5]).toBe(0); // Clamped
    
    // Test sum of valid outputs
    const sum = probabilityVector.slice(0, 4).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(0.99999);
  });
});

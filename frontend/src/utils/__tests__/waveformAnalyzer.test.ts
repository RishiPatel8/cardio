import { describe, it, expect } from 'vitest';
import { analyzeWaveform } from '../waveformAnalyzer';

describe('analyzeWaveform', () => {
  it('should return insufficient data message for undefined signal', () => {
    expect(analyzeWaveform(undefined)).toBe('Insufficient signal data for waveform pattern analysis.');
  });

  it('should return insufficient data message for short signal', () => {
    expect(analyzeWaveform(new Array(10).fill(0))).toBe('Insufficient signal data for waveform pattern analysis.');
  });

  it('should return low amplitude message for flatline signal', () => {
    expect(analyzeWaveform(new Array(250).fill(0.01))).toBe('Observed waveform characteristics show extremely low amplitude or near flatline, possibly indicating poor sensor contact or signal loss.');
  });

  it('should detect regular R-peaks with average intervals', () => {
    // Generate a synthetic 100Hz signal with regular peaks every 100 samples (1 second = 60 BPM)
    const signal = new Array(1000).fill(0);
    for (let i = 0; i < 1000; i++) {
      if (i % 100 === 0) {
        signal[i] = 1.0;
      } else {
        signal[i] = 0.1;
      }
    }
    const result = analyzeWaveform(signal);
    expect(result).toBe('Observed waveform characteristics include regular R-peak distribution and average RR intervals in the analyzed segment.');
  });

  it('should detect irregular rhythm (high RR variance)', () => {
    // Generate a synthetic signal with irregular peaks
    const signal = new Array(1000).fill(0);
    const peaks = [50, 120, 300, 400, 650, 750, 950];
    peaks.forEach(p => signal[p] = 1.0);
    
    const result = analyzeWaveform(signal);
    expect(result).toContain('periods of increased beat-to-beat irregularity');
  });

  it('should detect short RR intervals (high heart rate)', () => {
    // Generate a synthetic 100Hz signal with peaks every 40 samples (0.4s = 150 BPM)
    const signal = new Array(1000).fill(0);
    for (let i = 0; i < 1000; i++) {
      if (i % 40 === 0) {
        signal[i] = 1.0;
      } else {
        signal[i] = 0.1;
      }
    }
    const result = analyzeWaveform(signal);
    expect(result).toContain('unusually short RR intervals (elevated rate)');
  });
  
  it('should detect large amplitude variance', () => {
    // Generate a synthetic 100Hz signal with peaks every 100 samples
    const signal = new Array(1000).fill(0);
    for (let i = 0; i < 1000; i++) {
      if (i % 100 === 0) {
        signal[i] = 6.0; // Large amplitude
      } else {
        signal[i] = -0.5;
      }
    }
    const result = analyzeWaveform(signal);
    expect(result).toContain('unusually large waveform amplitudes');
  });
});

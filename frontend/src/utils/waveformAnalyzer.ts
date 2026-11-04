/**
 * Analyzes an ECG waveform segment and returns a descriptive string
 * based on measurable properties, without providing a clinical diagnosis.
 */
export const analyzeWaveform = (signal: number[] | undefined, sampleRate: number = 100): string => {
  if (!signal || signal.length < sampleRate * 2) {
    return "Insufficient signal data for waveform pattern analysis.";
  }

  // Basic stats
  let min = signal[0];
  let max = signal[0];
  let sum = 0;
  for (let i = 0; i < signal.length; i++) {
    const val = signal[i];
    if (val < min) min = val;
    if (val > max) max = val;
    sum += val;
  }
  const mean = sum / signal.length;
  const amplitudeRange = max - min;

  if (amplitudeRange < 0.1) {
    return "Observed waveform characteristics show extremely low amplitude or near flatline, possibly indicating poor sensor contact or signal loss.";
  }

  // Simple R-peak detection (detect peaks above 70% of max amplitude)
  const threshold = mean + 0.7 * (max - mean);
  const peaks: number[] = [];
  const minPeakDist = Math.floor(sampleRate * 0.4); // min 400ms between peaks (max 150 BPM)

  for (let i = 1; i < signal.length - 1; i++) {
    if (signal[i] > threshold && signal[i] >= signal[i - 1] && signal[i] >= signal[i + 1]) {
      if (peaks.length === 0 || (i - peaks[peaks.length - 1]) >= minPeakDist) {
        peaks.push(i);
      } else if (signal[i] > signal[peaks[peaks.length - 1]]) {
        // update to higher peak if too close
        peaks[peaks.length - 1] = i;
      }
    }
  }

  if (peaks.length < 2) {
    return "Observed waveform characteristics lack distinct repeating R-peaks, showing significant baseline variation or irregular morphology.";
  }

  // Calculate RR intervals in seconds
  const rrIntervals = [];
  for (let i = 1; i < peaks.length; i++) {
    rrIntervals.push((peaks[i] - peaks[i - 1]) / sampleRate);
  }

  const avgRR = rrIntervals.reduce((a, b) => a + b, 0) / rrIntervals.length;
  const rrVariance = rrIntervals.reduce((a, b) => a + Math.pow(b - avgRR, 2), 0) / rrIntervals.length;
  const rrStdDev = Math.sqrt(rrVariance);
  
  const bpm = 60 / avgRR;

  const characteristics: string[] = [];

  if (rrStdDev > 0.15) {
    characteristics.push("periods of increased beat-to-beat irregularity");
  } else {
    characteristics.push("regular R-peak distribution");
  }

  if (bpm > 100) {
    characteristics.push("unusually short RR intervals (elevated rate)");
  } else if (bpm < 50) {
    characteristics.push("unusually long RR intervals (depressed rate)");
  } else {
    characteristics.push("average RR intervals");
  }

  if (amplitudeRange > 5.0) {
    characteristics.push("unusually large waveform amplitudes");
  } else if (amplitudeRange < 0.5) {
    characteristics.push("reduced waveform amplitudes");
  }

  return `Observed waveform characteristics include ${characteristics.join(" and ")} in the analyzed segment.`;
};

import React, { useState, useEffect, useRef } from "react";

interface ArrhythmiaPreset {
  id: string;
  name: string;
  badge: string;
  color: string;
  confidence: number;
  bpm: number;
  rmssd: number;
  shapInterval: string;
  finding: string;
  probs: [number, number, number, number];
}

const PRESETS: ArrhythmiaPreset[] = [
  {
    id: "normal",
    name: "Normal Sinus Rhythm",
    badge: "PHYSIOLOGICAL",
    color: "#5856D6",
    confidence: 98.4,
    bpm: 72,
    rmssd: 44,
    shapInterval: "0.20s – 0.35s (P-Wave)",
    finding: "Synchronous SA nodal pacing with normal PR interval and narrow QRS complexes.",
    probs: [0.984, 0.008, 0.005, 0.003],
  },
  {
    id: "afib",
    name: "Atrial Fibrillation",
    badge: "HIGH RISK",
    color: "#FF9500",
    confidence: 96.1,
    bpm: 118,
    rmssd: 82,
    shapInterval: "Baseline Fibrillatory Waves",
    finding: "Absence of discrete P-waves with continuous chaotic baseline and irregular R-R cadence.",
    probs: [0.012, 0.961, 0.014, 0.013],
  },
  {
    id: "block",
    name: "Conduction Block",
    badge: "CONDUCTION DELAY",
    color: "#FF2D55",
    confidence: 94.7,
    bpm: 54,
    rmssd: 36,
    shapInterval: "1.15s – 1.38s (QRS Complex)",
    finding: "Broad notched QRS (>120ms) indicating delayed intraventricular impulse propagation.",
    probs: [0.018, 0.021, 0.947, 0.014],
  },
  {
    id: "other",
    name: "Other Arrhythmia (Ischemia/Strain)",
    badge: "REPOLARIZATION STRAIN",
    color: "#007AFF",
    confidence: 91.5,
    bpm: 84,
    rmssd: 31,
    shapInterval: "5.85s – 6.10s (ST-T Wave)",
    finding: "Significant ST-segment depression with deep asymmetric T-wave repolarization inversion.",
    probs: [0.035, 0.025, 0.025, 0.915],
  },
];

export const LiveTelemetrySimulator: React.FC = () => {
  const [activePreset, setActivePreset] = useState<ArrhythmiaPreset>(PRESETS[2]); // Default to Conduction Block
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Generate synthetic waveform points based on preset
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let offset = 0;

    const render = () => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      // 1. Standard ECG Grid
      ctx.strokeStyle = "rgba(254, 215, 170, 0.22)"; // Peach minor grid
      ctx.lineWidth = 0.5;
      const gridSize = 16;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Major grid (every 5 boxes = 80px)
      ctx.strokeStyle = "rgba(253, 186, 116, 0.4)";
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += gridSize * 5) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize * 5) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // 2. Waveform generation
      ctx.beginPath();
      ctx.strokeStyle = "#FFFFFF";
      ctx.lineWidth = 2.2;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";

      const cy = h / 2;
      const points: [number, number][] = [];

      for (let x = 0; x < w; x++) {
        const t = (x + offset) * 0.02;
        let y = 0;

        if (activePreset.id === "normal") {
          // Regular sinus
          const phase = t % 2.5;
          if (phase > 0.4 && phase < 0.6) y += Math.sin((phase - 0.4) * 5 * Math.PI) * 14; // P
          if (phase >= 0.9 && phase <= 1.05) { // QRS
            const q = (phase - 0.97) * 40;
            y -= Math.exp(-q * q) * 65;
          }
          if (phase > 1.3 && phase < 1.7) y += Math.sin((phase - 1.3) * 2.5 * Math.PI) * 22; // T
        } else if (activePreset.id === "afib") {
          // Chaotic baseline fibrillatory waves + irregular QRS
          const fWave = Math.sin(t * 18) * 6 + Math.cos(t * 26) * 4;
          y += fWave;
          const phase = (t + Math.sin(t * 0.5) * 1.5) % 2.0;
          if (phase >= 0.7 && phase <= 0.85) {
            const q = (phase - 0.77) * 45;
            y -= Math.exp(-q * q) * 60;
          }
        } else if (activePreset.id === "block") {
          // Wide notched QRS
          const phase = t % 3.0;
          if (phase > 0.3 && phase < 0.6) y += Math.sin((phase - 0.3) * 3.3 * Math.PI) * 12; // PR delay
          if (phase >= 1.0 && phase <= 1.35) { // Broad notched QRS
            const q1 = (phase - 1.1) * 30;
            const q2 = (phase - 1.25) * 30;
            y -= Math.exp(-q1 * q1) * 55 + Math.exp(-q2 * q2) * 50;
          }
          if (phase > 1.5 && phase < 1.9) y -= Math.sin((phase - 1.5) * 2.5 * Math.PI) * 18; // Inverted T
        } else {
          // ST depression / Strain
          const phase = t % 2.4;
          if (phase > 0.3 && phase < 0.55) y += Math.sin((phase - 0.3) * 4 * Math.PI) * 12;
          if (phase >= 0.8 && phase <= 0.95) {
            const q = (phase - 0.87) * 40;
            y -= Math.exp(-q * q) * 65;
          }
          if (phase > 0.95 && phase < 1.35) y += 18; // ST depression
          if (phase >= 1.35 && phase < 1.7) y -= Math.sin((phase - 1.35) * 2.8 * Math.PI) * 24; // Inverted T
        }

        points.push([x, cy + y]);
      }

      // Draw Waveform
      points.forEach(([x, y], idx) => {
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Draw SHAP Salient Region Highlight
      ctx.save();
      ctx.fillStyle = "rgba(255, 45, 85, 0.22)";
      ctx.beginPath();
      const highlightStart = (w * 0.38 - offset * 0.5) % w;
      const highlightWidth = 90;
      ctx.rect(highlightStart, 0, highlightWidth, h);
      ctx.fill();
      ctx.strokeStyle = "rgba(255, 45, 85, 0.7)";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(highlightStart, 0, highlightWidth, h);
      ctx.restore();

      // Lead Text Banner
      ctx.font = "bold 11px Inter, sans-serif";
      ctx.fillStyle = "#94A3B8";
      ctx.fillText("Lead MLII — Standard 25 mm/s Clinical Telemetry Strip (100 Hz)", 16, 22);

      offset += 1.8;
      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [activePreset]);

  return (
    <div
      style={{
        background: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "20px",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
      }}
    >
      {/* Selector Pills */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase", marginRight: "6px" }}>
          Interactive Rhythm Presets:
        </span>
        {PRESETS.map((p) => {
          const isActive = activePreset.id === p.id;
          return (
            <button
              key={p.id}
              onClick={() => setActivePreset(p)}
              style={{
                padding: "8px 16px",
                borderRadius: "30px",
                border: `1px solid ${isActive ? p.color : "rgba(255, 255, 255, 0.1)"}`,
                background: isActive ? `${p.color}25` : "rgba(255, 255, 255, 0.03)",
                color: isActive ? "#FFFFFF" : "var(--text-secondary)",
                fontSize: "0.8rem",
                fontWeight: "600",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                cursor: "pointer",
                transition: "all 0.25s ease",
              }}
            >
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: p.color }} />
              {p.name}
            </button>
          );
        })}
      </div>

      {/* Rhythm Strip Canvas */}
      <div style={{ position: "relative", borderRadius: "14px", overflow: "hidden", border: "1px solid rgba(255, 255, 255, 0.06)", background: "#090D16" }}>
        <canvas ref={canvasRef} width={820} height={190} style={{ width: "100%", height: "190px", display: "block" }} />
        
        {/* Real-time Badge Overlay */}
        <div style={{ position: "absolute", top: "12px", right: "14px", display: "flex", gap: "8px" }}>
          <span
            style={{
              padding: "4px 10px",
              borderRadius: "6px",
              background: `${activePreset.color}22`,
              border: `1px solid ${activePreset.color}55`,
              color: activePreset.color,
              fontSize: "0.7rem",
              fontWeight: "700",
              letterSpacing: "0.5px",
            }}
          >
            {activePreset.badge}
          </span>
          <span style={{ padding: "4px 10px", borderRadius: "6px", background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#10B981", fontSize: "0.7rem", fontWeight: "700" }}>
            SNR: 24.6 dB (EXCELLENT)
          </span>
        </div>
      </div>

      {/* Real-time Diagnostic & Attribution Output */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
        <div style={{ padding: "14px 18px", borderRadius: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase" }}>AI Confidence Score</div>
          <div style={{ fontSize: "1.4rem", fontWeight: "900", color: activePreset.color, marginTop: "4px" }}>
            {activePreset.confidence}%
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Ensemble Consensus (7 Models)
          </div>
        </div>

        <div style={{ padding: "14px 18px", borderRadius: "12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase" }}>Autonomic Vitals</div>
          <div style={{ fontSize: "1.2rem", fontWeight: "800", color: "#FFFFFF", marginTop: "4px" }}>
            {activePreset.bpm} BPM &bull; {activePreset.rmssd} ms
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Calculated RMSSD HRV Marker
          </div>
        </div>

        <div style={{ padding: "14px 18px", borderRadius: "12px", background: "rgba(255, 45, 85, 0.06)", border: "1px solid rgba(255, 45, 85, 0.2)" }}>
          <div style={{ fontSize: "0.7rem", color: "#FF2D55", fontWeight: "700", textTransform: "uppercase" }}>Top SHAP Salient Region</div>
          <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#FFFFFF", marginTop: "4px" }}>
            {activePreset.shapInterval}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
            {activePreset.finding}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveTelemetrySimulator;

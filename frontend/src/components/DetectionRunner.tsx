import React, { useState, useEffect } from "react";
import { Cpu, Play, Zap } from "lucide-react";

interface DetectionRunnerProps {
  hasData: boolean;
  onStartAnalysis: () => void;
  onAnalysisComplete: () => void;
  isAnalyzing: boolean;
  availableModels: any[];
  selectedModelId: string;
  onModelSelect: (id: string) => void;
}

const stages = [
  "Parsing ECG sequence arrays...",
  "Computing HRV parameters (RMSSD, SDRR)...",
  "Running neural network classifier model...",
  "Cross-referencing ECG anomaly patterns...",
  "Finalizing confidence metrics...",
];

export const DetectionRunner: React.FC<DetectionRunnerProps> = ({
  hasData,
  onStartAnalysis,
  onAnalysisComplete,
  isAnalyzing,
  availableModels,
  selectedModelId,
  onModelSelect,
}) => {
  const [analysisStage, setAnalysisStage] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {
    if (!isAnalyzing) {
      setProgress(0);
      setAnalysisStage(0);
      return;
    }

    // Proactively animate analysis stages
    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += 4;
      if (currentProgress > 100) {
        currentProgress = 100;
      }
      setProgress(currentProgress);

      // Map progress to stage index
      const stageIdx = Math.min(
        stages.length - 1,
        Math.floor((currentProgress / 100) * stages.length)
      );
      setAnalysisStage(stageIdx);

      if (currentProgress === 100) {
        clearInterval(interval);
        setTimeout(() => {
          onAnalysisComplete();
        }, 200);
      }
    }, 20);

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  return (
    <div className={`glass-panel ${isAnalyzing ? "pulse-glow-violet" : ""}`} style={{ position: "relative", overflow: "hidden" }}>
      {/* Background glowing AI grid lines */}
      <div
        className="grid-bg"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: "none",
          opacity: isAnalyzing ? 0.35 : 0.1,
          zIndex: 1,
        }}
      />

      <div style={{ position: "relative", zIndex: 2, display: "flex", flexDirection: "column", gap: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              padding: "10px",
              borderRadius: "10px",
              background: isAnalyzing ? "rgba(139, 92, 246, 0.15)" : "rgba(255, 255, 255, 0.05)",
              color: isAnalyzing ? "var(--color-primary)" : "var(--text-secondary)",
              transition: "var(--transition-smooth)",
            }}
          >
            <Cpu size={24} className={isAnalyzing ? "heartbeat-animation" : ""} />
          </div>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: "700", color: "#FFFFFF" }}>AI Risk Diagnostics</h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "2px" }}>
              Analyses heart intervals using CardioGuard classifier weights.
            </p>
          </div>
        </div>

        {!isAnalyzing ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {!hasData && (
              <div
                style={{
                  padding: "12px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(245, 158, 11, 0.06)",
                  border: "1px solid rgba(245, 158, 11, 0.15)",
                  fontSize: "0.8rem",
                  color: "var(--color-warning)",
                  lineHeight: "1.4",
                }}
              >
                No telemetry loaded. Connect Google Fit or upload a PhysioNet CSV file above to enable detection.
              </div>
            )}
            
            {/* Model Selection Dropdown */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Selected Engine</label>
              <select 
                value={selectedModelId}
                onChange={(e) => onModelSelect(e.target.value)}
                disabled={!hasData || isAnalyzing}
                style={{
                  width: "100%",
                  padding: "10px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid var(--border-glass)",
                  color: "#FFFFFF",
                  fontSize: "0.9rem",
                  outline: "none",
                  cursor: "pointer"
                }}
              >
                <option value="default" style={{ color: "#000" }}>Current Model (v6-canonical)</option>
                <option value="compare" style={{ color: "#000", fontWeight: "bold" }}>⚡ Compare All Enabled Models</option>
                <optgroup label="Individual Verified Models" style={{ color: "#000" }}>
                  {availableModels.map(m => (
                    <option key={m.id} value={m.id} style={{ color: "#000" }}>
                      {m.architecture} ({m.version})
                    </option>
                  ))}
                </optgroup>
              </select>
            </div>

            <button
              onClick={onStartAnalysis}
              disabled={!hasData}
              className="btn-primary"
              style={{
                width: "100%",
                justifyContent: "center",
                padding: "16px",
                fontSize: "1.05rem",
                boxShadow: hasData ? "0 0 20px rgba(139, 92, 246, 0.3)" : "none",
              }}
            >
              <Play size={18} fill="currentColor" />
              Run AI Detection
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", padding: "10px 0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#FFFFFF" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: "600" }}>
                <Zap size={14} style={{ color: "var(--color-primary)", animation: "pulse-glow 1s infinite" }} />
                {stages[analysisStage]}
              </span>
              <span style={{ fontWeight: "700", color: "var(--color-primary)" }}>{progress}%</span>
            </div>

            {/* Glowing progress bar */}
            <div
              style={{
                width: "100%",
                height: "8px",
                background: "rgba(255, 255, 255, 0.05)",
                borderRadius: "4px",
                overflow: "hidden",
                boxShadow: "inset 0 1px 3px rgba(0,0,0,0.5)",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${progress}%`,
                  background: "linear-gradient(to right, var(--color-primary), var(--color-secondary))",
                  boxShadow: "0 0 10px var(--color-primary-glow)",
                  borderRadius: "4px",
                  transition: "width 0.1s ease-out",
                }}
              />
            </div>

            {/* ECG Simulator Canvas */}
            <div
              style={{
                width: "100%",
                height: "60px",
                borderRadius: "8px",
                backgroundColor: "rgba(0, 0, 0, 0.3)",
                border: "1px solid rgba(255, 255, 255, 0.05)",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <svg width="100%" height="100%" viewBox="0 0 400 60">
                <path
                  d={`M 0 30 L 50 30 L 60 20 L 70 40 L 80 30 L 120 30 L 130 10 L 140 50 L 150 30 L 200 30 L 210 20 L 220 40 L 230 30 L 280 30 L 290 5 L 300 55 L 310 30 L 400 30`}
                  fill="none"
                  stroke="var(--color-primary)"
                  strokeWidth="2"
                  strokeDasharray="400"
                  strokeDashoffset={400 - (progress / 100) * 400}
                  style={{ transition: "stroke-dashoffset 0.1s linear" }}
                />
              </svg>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

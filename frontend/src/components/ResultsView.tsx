import React, { useState } from "react";
import { ShieldCheck, ShieldAlert, FileText, Info, Loader2 } from "lucide-react";

interface ResultsViewProps {
  resultType: "normal" | "af";
  confidence: number;
  modelVersion: string;
  explainableInsights: string[];
  inferenceTimeMs: number;
  onReset: () => void;
  onExportReport: () => Promise<void>;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  resultType,
  confidence,
  modelVersion,
  explainableInsights,
  inferenceTimeMs,
  onReset,
  onExportReport,
}) => {
  const isAF = resultType === "af";
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await onExportReport();
    } catch (e) {
      console.error(e);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "18px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h4 style={{ fontSize: "1rem", fontWeight: "700", color: "#FFFFFF" }}>AI Diagnostic Output</h4>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Research-Grade Inference</span>
        </div>
        <button
          onClick={onReset}
          style={{
            fontSize: "0.7rem",
            color: "var(--text-muted)",
            background: "none",
            border: "none",
            cursor: "pointer",
            fontWeight: "700"
          }}
        >
          Reset
        </button>
      </div>

      {/* Main classification card */}
      <div 
        style={{ 
          display: "flex", 
          flexDirection: "column",
          gap: "14px",
          backgroundColor: "rgba(255, 255, 255, 0.02)", 
          border: `1px solid ${isAF ? "rgba(255, 45, 85, 0.15)" : "rgba(52, 199, 89, 0.15)"}`,
          padding: "16px", 
          borderRadius: "14px" 
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {isAF ? (
              <ShieldAlert size={22} color="#FF2D55" />
            ) : (
              <ShieldCheck size={22} color="#34C759" />
            )}
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "0.9rem", color: "#FFFFFF", fontWeight: "700" }}>
                {isAF ? "AF Risk Flagged" : "Normal Sinus Rhythm"}
              </span>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                Model: {modelVersion} • {inferenceTimeMs}ms
              </span>
            </div>
          </div>
          
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={handleExport}
              disabled={isExporting}
              style={{ padding: "8px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255,255,255,0.04)", cursor: "pointer", display: "flex", alignItems: "center" }}
              title="Generate PDF Report"
            >
              {isExporting ? <Loader2 size={14} className="spin-animation" /> : <FileText size={14} color="#FFFFFF" />}
            </button>
          </div>
        </div>

        {/* Confidence Progress Bar */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
            <span style={{ color: "var(--text-secondary)" }}>Classification Confidence</span>
            <span style={{ fontWeight: "700", color: isAF ? "#FF2D55" : "#34C759" }}>{confidence.toFixed(1)}%</span>
          </div>
          <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
            <div 
              style={{ 
                width: `${confidence}%`, 
                height: "100%", 
                backgroundColor: isAF ? "#FF2D55" : "#34C759",
                transition: "width 0.5s ease-out" 
              }} 
            />
          </div>
        </div>
      </div>

      {/* SHAP & Explainable AI Insights list */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", fontWeight: "700", color: "var(--text-secondary)" }}>
          <Info size={14} />
          <span>Explainable AI (XAI) Justifications</span>
        </div>
        <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
          {explainableInsights.map((insight, idx) => (
            <li 
              key={idx} 
              style={{ 
                fontSize: "0.75rem", 
                color: "var(--text-secondary)", 
                lineHeight: "1.4",
                padding: "10px 12px",
                borderRadius: "10px",
                backgroundColor: "rgba(255, 255, 255, 0.01)",
                borderLeft: `2px solid ${isAF ? "rgba(255, 45, 85, 0.4)" : "rgba(52, 199, 89, 0.4)"}`
              }}
            >
              {insight}
            </li>
          ))}
        </ul>
      </div>

      <style>{`
        .spin-animation {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

import React, { useState } from "react";
import { ShieldCheck, ShieldAlert, FileText, Info, Loader2 } from "lucide-react";
import { analyzeWaveform } from "../utils/waveformAnalyzer";

const formatNumber = (value: unknown, decimals = 1, fallback = "—"): string => {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(decimals)
    : fallback;
};

interface ResultsViewProps {
  resultType: string;
  confidence: number;
  modelVersion: string;
  explanationValues?: any[];
  inferenceTimeMs: number;
  probabilityVector?: number[];
  signalQuality?: string;
  onReset: () => void;
  onExportReport: () => Promise<void>;
  onRegionClick?: (startSec: number, endSec: number) => void;
  highestRiskSegment?: number[];
  comparisons?: any[];
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  resultType,
  confidence,
  modelVersion,
  explanationValues,
  inferenceTimeMs,
  probabilityVector,
  signalQuality,
  onReset,
  onExportReport,
  onRegionClick,
  highestRiskSegment,
  comparisons,
}) => {
  const isAnomaly = resultType !== "Normal Sinus Rhythm";
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

  // Group SHAP/gradient attribution values into continuous time regions
  const areasOfInterest = React.useMemo(() => {
    // 1. Filter for positive contributions and extract time index
    const positiveFeatures = (explanationValues || [])
      .filter((v: any) => v.contribution > 0.0001 && v.feature && v.feature.startsWith('time_'))
      .map((v: any) => {
        const sampleIdx = parseInt(v.feature.split('_')[1], 10);
        return {
          index: sampleIdx,
          timeSec: sampleIdx / 100.0,
          contribution: v.contribution
        };
      })
      .filter((v: any) => !isNaN(v.index))
      .sort((a: any, b: any) => a.index - b.index);

    if (positiveFeatures.length > 0) {
      // Select the top N strongest attributions to focus on salient clusters
      const sortedByVal = [...positiveFeatures].sort((a, b) => b.contribution - a.contribution);
      const topCount = Math.min(25, Math.max(3, Math.floor(positiveFeatures.length * 0.1)));
      const threshold = sortedByVal[topCount - 1]?.contribution || 0;
      const keyFeatures = positiveFeatures.filter((v: any) => v.contribution >= threshold);

      if (keyFeatures.length > 0) {
        // Group nearby points (within 0.5s of each other)
        const regions: { start: number; end: number; maxContrib: number }[] = [];
        let currentRegion = { start: keyFeatures[0].timeSec, end: keyFeatures[0].timeSec, maxContrib: keyFeatures[0].contribution };

        for (let i = 1; i < keyFeatures.length; i++) {
          const pt = keyFeatures[i];
          if (pt.timeSec - currentRegion.end <= 0.5) {
            currentRegion.end = pt.timeSec;
            currentRegion.maxContrib = Math.max(currentRegion.maxContrib, pt.contribution);
          } else {
            regions.push(currentRegion);
            currentRegion = { start: pt.timeSec, end: pt.timeSec, maxContrib: pt.contribution };
          }
        }
        regions.push(currentRegion);

        const mapped = regions.map(r => {
          if (r.start === r.end) {
            return { 
              start: Math.max(0, parseFloat((r.start - 0.1).toFixed(2))), 
              end: parseFloat((r.end + 0.1).toFixed(2)), 
              maxContrib: r.maxContrib 
            };
          }
          return {
            start: parseFloat(r.start.toFixed(2)),
            end: parseFloat(r.end.toFixed(2)),
            maxContrib: r.maxContrib
          };
        }).sort((a, b) => b.maxContrib - a.maxContrib).slice(0, 3);

        if (mapped.length > 0) return mapped;
      }
    }

    // Fallback: If no regions could be grouped from explanationValues, identify top peak regions from highestRiskSegment
    if (highestRiskSegment && highestRiskSegment.length >= 100) {
      const seg = highestRiskSegment;
      const mean = seg.reduce((a, b) => a + b, 0) / seg.length;
      const std = Math.sqrt(seg.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / seg.length);
      const peakThresh = mean + Math.max(std * 1.0, 0.2);
      const minPeakDist = 40; // 400ms at 100Hz
      const peaks: { timeSec: number; val: number }[] = [];

      for (let i = 1; i < seg.length - 1; i++) {
        if (seg[i] > peakThresh && seg[i] >= seg[i - 1] && seg[i] >= seg[i + 1]) {
          if (peaks.length === 0 || (i - (peaks[peaks.length - 1].timeSec * 100)) >= minPeakDist) {
            peaks.push({ timeSec: i / 100.0, val: seg[i] });
          }
        }
      }

      if (peaks.length > 0) {
        return peaks.slice(0, 3).map(p => ({
          start: Math.max(0, parseFloat((p.timeSec - 0.15).toFixed(2))),
          end: Math.min(10.0, parseFloat((p.timeSec + 0.15).toFixed(2))),
          maxContrib: p.val
        }));
      }
    }

    return [];
  }, [explanationValues, highestRiskSegment]);

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
          border: `1px solid ${isAnomaly ? "rgba(255, 45, 85, 0.15)" : "rgba(52, 199, 89, 0.15)"}`,
          padding: "16px", 
          borderRadius: "14px" 
        }}
      >
        {comparisons && comparisons.length > 0 ? (
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <ShieldCheck size={22} color="#007AFF" />
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "0.9rem", color: "#FFFFFF", fontWeight: "700" }}>
                  Multi-Model Consensus Report
                </span>
                <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                  Models evaluated: {comparisons.length}
                </span>
              </div>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {comparisons.map((c: any, i: number) => {
                const cAnomaly = c.classification !== "Normal Sinus Rhythm" && c.classification !== "normal";
                return (
                  <div key={i} style={{ 
                    display: "flex", alignItems: "center", justifyContent: "space-between", 
                    padding: "10px", borderRadius: "8px", 
                    background: "rgba(255,255,255,0.03)", 
                    border: "1px solid var(--border-glass)" 
                  }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontSize: "0.8rem", fontWeight: "700", color: "#FFFFFF" }}>{c.model_id}</span>
                      <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>{c.architecture || c.model_version}</span>
                    </div>
                    {c.status === "success" ? (
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "0.85rem", fontWeight: "800", color: cAnomaly ? "#FF2D55" : "#34C759" }}>
                          {c.classification || c.prediction?.label}
                        </div>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                          Confidence: {(c.confidence_score !== undefined ? c.confidence_score : c.prediction?.confidence * 100).toFixed(1)}% | {c.inference_time_ms}ms
                        </div>
                      </div>
                    ) : (
                      <div style={{ fontSize: "0.8rem", color: "#FF9500" }}>Failed: {c.status}</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                {isAnomaly ? (
                  <ShieldAlert size={22} color="#FF2D55" />
                ) : (
                  <ShieldCheck size={22} color="#34C759" />
                )}
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.9rem", color: "#FFFFFF", fontWeight: "700" }}>
                    Predicted Class: {resultType}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                    Model: {modelVersion} • Inference Latency: {inferenceTimeMs}ms
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
                <span style={{ color: "var(--text-secondary)" }}>Predicted Class Probability</span>
                <span style={{ fontWeight: "700", color: isAnomaly ? "#FF2D55" : "#34C759" }}>{formatNumber(confidence, 1)}%</span>
              </div>
              <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
                <div 
                  style={{ 
                    width: `${confidence}%`, 
                    height: "100%", 
                    backgroundColor: isAnomaly ? "#FF2D55" : "#34C759",
                    transition: "width 0.5s ease-out" 
                  }} 
                />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Probability Vector Chart */}
      {probabilityVector && probabilityVector.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", fontWeight: "700", color: "var(--text-secondary)" }}>
              <Info size={14} />
              <span>Class Probability Distribution</span>
            </div>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginLeft: "20px" }}>
              {modelVersion} predicted probability for each classification.
            </span>
          </div>
          <div style={{ width: "100%", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
            {["Normal Sinus Rhythm", "Atrial Fibrillation (AFIB)", "Conduction Block", "Other Arrhythmia"].map((className, idx) => {
              const val = (probabilityVector[idx] || 0) * 100;
              return (
                <div key={className} style={{ display: "flex", alignItems: "center", gap: "12px", width: "100%" }}>
                  <div style={{ width: "160px", flexShrink: 0, fontSize: "0.75rem", color: "var(--text-secondary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {className}
                  </div>
                  <div style={{ flexGrow: 1, height: "14px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px", overflow: "hidden" }}>
                    <div style={{ width: `${val}%`, height: "100%", backgroundColor: ["#5856D6", "#FF9500", "#FF2D55", "#007AFF"][idx], borderRadius: "4px", transition: "width 0.5s ease-out" }} />
                  </div>
                  <div style={{ width: "45px", flexShrink: 0, fontSize: "0.75rem", fontWeight: "700", color: "#FFFFFF", textAlign: "right" }}>
                    {formatNumber(val, 1)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ECG Signal Findings */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.85rem", fontWeight: "800", color: "#FFFFFF", textTransform: "uppercase" }}>
          <Info size={16} />
          <span>ECG Signal Findings</span>
        </div>
        
        {/* Signal Meta Info */}
        <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "#FFFFFF", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "10px", padding: "12px", whiteSpace: "pre", overflowX: "auto" }}>
{`┌─────────────────────────────────────────────────────────────┐
│ SIGNAL QUALITY       ANALYZED WINDOW       SAMPLING RATE    │
│ ${(signalQuality || "UNKNOWN").padEnd(20)} 0.0s – 10.0s          100 Hz           │
└─────────────────────────────────────────────────────────────┘`}
        </div>

        {/* Signal Pattern */}
        <div style={{ padding: "12px", backgroundColor: "rgba(255,255,255,0.01)", borderRadius: "10px", display: "flex", flexDirection: "column", gap: "4px" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "700" }}>Signal Pattern</span>
          <span style={{ fontSize: "0.75rem", color: "#FFFFFF", lineHeight: "1.4" }}>
            {analyzeWaveform(highestRiskSegment)}
          </span>
        </div>

        {/* Areas of Interest */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "700" }}>Areas of Interest</span>
          {areasOfInterest.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {areasOfInterest.map((region, idx) => (
                <div 
                  key={idx} 
                  style={{ 
                    display: "flex", 
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "10px 12px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(255, 255, 255, 0.02)",
                    borderLeft: `2px solid ${isAnomaly ? "rgba(255, 45, 85, 0.4)" : "rgba(52, 199, 89, 0.4)"}`
                  }}
                >
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#FFFFFF" }}>{formatNumber(region.start, 2)}s – {formatNumber(region.end, 2)}s</span>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Higher model attribution</span>
                  </div>
                  {onRegionClick && (
                    <button
                      onClick={() => onRegionClick(region.start, region.end)}
                      style={{
                        padding: "4px 8px",
                        fontSize: "0.65rem",
                        fontWeight: "700",
                        color: "var(--color-primary)",
                        backgroundColor: "rgba(0, 122, 255, 0.1)",
                        border: "1px solid rgba(0, 122, 255, 0.3)",
                        borderRadius: "6px",
                        cursor: "pointer"
                      }}
                    >
                      View on ECG
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: "10px 12px", fontSize: "0.75rem", color: "var(--text-muted)", backgroundColor: "rgba(255,255,255,0.01)", borderRadius: "10px" }}>
              No significant attribution regions identified.
            </div>
          )}
        </div>

        {/* Model Finding */}
        <div style={{ padding: "12px", backgroundColor: "rgba(255,255,255,0.01)", borderRadius: "10px", display: "flex", flexDirection: "column", gap: "4px" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "700" }}>Model Finding</span>
          <span style={{ fontSize: "0.75rem", color: "#FFFFFF", lineHeight: "1.4" }}>
            The {modelVersion} model assigned the highest prediction probability to <strong>{resultType}</strong>. The highlighted waveform regions represent areas with stronger model attribution for this prediction.
          </span>
        </div>
      </div>

      {/* Clinical Disclaimer */}
      <div style={{ marginTop: "8px", padding: "12px", borderRadius: "10px", backgroundColor: "rgba(255, 149, 0, 0.05)", border: "1px solid rgba(255, 149, 0, 0.2)" }}>
        <h5 style={{ fontSize: "0.7rem", fontWeight: "800", color: "#FF9500", textTransform: "uppercase", marginBottom: "4px" }}>Research Disclaimer</h5>
        <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", lineHeight: "1.4", margin: 0 }}>
          Model attribution indicates which portions of the input influenced the prediction.<br/>
          It does not establish clinical causality or constitute a medical diagnosis.
        </p>
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

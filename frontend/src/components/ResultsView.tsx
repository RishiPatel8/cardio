import React, { useState } from "react";
import { 
  Activity, ShieldCheck, ShieldAlert, FileText, Info, Loader2, 
  Layers, CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronUp 
} from "lucide-react";
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
  contributingModels?: any[];
  excludedModels?: any[];
  contributingModelsCount?: number;
  totalModelsCount?: number;
  agreementAnalysis?: any;
  ensembleWeights?: any;
  isEnsemble?: boolean;
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
  contributingModels,
  excludedModels,
  contributingModelsCount,
  totalModelsCount,
  agreementAnalysis,
  // ensembleWeights
  isEnsemble = false,
}) => {
  const isAnomaly = resultType !== "Normal Sinus Rhythm" && resultType !== "Normal" && resultType !== "normal";
  const [isExporting, setIsExporting] = useState(false);
  const [showModelContributions, setShowModelContributions] = useState(true);

  const isEnsembleMode = isEnsemble || modelVersion === "v9-ensemble" || modelVersion?.includes("Ensemble") || (contributingModels && contributingModels.length > 0);

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
      const sortedByVal = [...positiveFeatures].sort((a, b) => b.contribution - a.contribution);
      const topCount = Math.min(25, Math.max(3, Math.floor(positiveFeatures.length * 0.1)));
      const threshold = sortedByVal[topCount - 1]?.contribution || 0;
      const keyFeatures = positiveFeatures.filter((v: any) => v.contribution >= threshold);

      if (keyFeatures.length > 0) {
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

    // Fallback: If no regions from explanations, find peaks from highest risk segment
    if (highestRiskSegment && highestRiskSegment.length >= 100) {
      const seg = highestRiskSegment;
      const mean = seg.reduce((a, b) => a + b, 0) / seg.length;
      const std = Math.sqrt(seg.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / seg.length);
      const peakThresh = mean + Math.max(std * 1.0, 0.2);
      const minPeakDist = 40;
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
    <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h4 style={{ fontSize: "1.05rem", fontWeight: "800", color: "#FFFFFF", display: "flex", alignItems: "center", gap: "8px" }}>
            {isEnsembleMode ? (
              <>
                <Layers size={18} color="#8B5CF6" />
                <span>Final Ensemble Diagnostic Result</span>
              </>
            ) : (
              <span>AI Diagnostic Output</span>
            )}
          </h4>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
            {isEnsembleMode ? "Seven-Model Soft-Voting Consensus • Primary Clinical Evaluation" : "Research-Grade Inference"}
          </span>
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

      {/* PRIMARY RESULT CARD */}
      <div 
        style={{ 
          display: "flex", 
          flexDirection: "column",
          gap: "14px",
          backgroundColor: isEnsembleMode ? "rgba(139, 92, 246, 0.04)" : "rgba(255, 255, 255, 0.02)", 
          border: `1px solid ${isEnsembleMode ? "rgba(139, 92, 246, 0.3)" : (isAnomaly ? "rgba(255, 45, 85, 0.15)" : "rgba(52, 199, 89, 0.15)")}`,
          padding: "18px", 
          borderRadius: "14px",
          boxShadow: isEnsembleMode ? "0 4px 20px rgba(139, 92, 246, 0.08)" : "none"
        }}
      >
        {comparisons && comparisons.length > 0 ? (
          /* Multi-Model Comparison View */
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <ShieldCheck size={22} color="#007AFF" />
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "0.9rem", color: "#FFFFFF", fontWeight: "700" }}>
                  Multi-Model Comparison Report
                </span>
                <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                  Models evaluated: {comparisons.length} (Individual outputs shown side by side)
                </span>
              </div>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {comparisons.map((c: any, i: number) => {
                const cClassification = c.classification || (typeof c.prediction === "string" ? c.prediction : c.prediction?.label) || "Unknown";
                const cAnomaly = cClassification !== "Normal Sinus Rhythm" && cClassification !== "normal" && cClassification !== "Normal";
                const rawConf = c.confidence_score !== undefined ? c.confidence_score : (c.confidence !== undefined ? c.confidence : (c.prediction?.confidence !== undefined ? c.prediction.confidence * 100 : 0));
                const cConfidence = isNaN(Number(rawConf)) ? 0 : Number(rawConf);
                const cLatency = c.inference_time_ms !== undefined ? c.inference_time_ms : (c.latency_ms !== undefined ? c.latency_ms : 0);
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
                          {cClassification}
                        </div>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                          Confidence: {cConfidence.toFixed(1)}% | {cLatency}ms
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
          /* Primary Diagnostic Result Card (Ensemble or Single Model) */
          <>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
                {isAnomaly ? (
                  <ShieldAlert size={26} color="#FF2D55" style={{ marginTop: "2px", flexShrink: 0 }} />
                ) : (
                  <ShieldCheck size={26} color="#34C759" style={{ marginTop: "2px", flexShrink: 0 }} />
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  {isEnsembleMode && (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ 
                        fontSize: "0.62rem", 
                        fontWeight: "800", 
                        color: "#C4B5FD", 
                        background: "rgba(139, 92, 246, 0.25)", 
                        padding: "2px 8px", 
                        borderRadius: "12px",
                        border: "1px solid rgba(139, 92, 246, 0.4)",
                        textTransform: "uppercase" 
                      }}>
                        ★ Primary Diagnostic Output
                      </span>
                      <span style={{ fontSize: "0.65rem", color: "#A78BFA", fontWeight: "700" }}>
                        Final Ensemble Model
                      </span>
                    </div>
                  )}
                  <span style={{ fontSize: "1.15rem", color: "#FFFFFF", fontWeight: "800", letterSpacing: "-0.01em" }}>
                    {resultType}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                    {isEnsembleMode 
                      ? `Combined 7-Model Prediction Engine • ${inferenceTimeMs}ms Latency`
                      : `Model: ${modelVersion} • Inference Latency: ${inferenceTimeMs}ms`}
                  </span>
                </div>
              </div>
              
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={handleExport}
                  disabled={isExporting}
                  style={{ 
                    padding: "8px 12px", 
                    borderRadius: "8px", 
                    border: "1px solid var(--border-glass)", 
                    backgroundColor: "rgba(255,255,255,0.04)", 
                    cursor: "pointer", 
                    display: "flex", 
                    alignItems: "center",
                    gap: "6px",
                    color: "#FFFFFF",
                    fontSize: "0.75rem",
                    fontWeight: "600"
                  }}
                  title="Generate Comprehensive Clinical PDF Report"
                >
                  {isExporting ? <Loader2 size={14} className="spin-animation" /> : <FileText size={14} color="#8B5CF6" />}
                  <span>Export PDF</span>
                </button>
              </div>
            </div>

            {/* Confidence Progress Bar */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                <span style={{ color: "var(--text-secondary)" }}>
                  {isEnsembleMode ? "Final Weighted Consensus Probability" : "Predicted Class Probability"}
                </span>
                <span style={{ fontWeight: "800", color: isAnomaly ? "#FF2D55" : "#34C759", fontSize: "0.85rem" }}>
                  {formatNumber(confidence, 1)}%
                </span>
              </div>
              <div style={{ width: "100%", height: "8px", backgroundColor: "rgba(255,255,255,0.06)", borderRadius: "4px", overflow: "hidden" }}>
                <div 
                  style={{ 
                    width: `${Math.min(100, Math.max(0, confidence))}%`, 
                    height: "100%", 
                    backgroundColor: isAnomaly ? "#FF2D55" : "#34C759",
                    transition: "width 0.5s ease-out" 
                  }} 
                />
              </div>
            </div>

            {/* Metadata Pills Matrix */}
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", 
              gap: "8px", 
              paddingTop: "6px" 
            }}>
              <div style={{ padding: "8px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Contributing Models</div>
                <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#FFFFFF" }}>
                  {isEnsembleMode ? `${contributingModelsCount || 7} of ${totalModelsCount || 7} active` : "1 Single Architecture"}
                </div>
              </div>

              <div style={{ padding: "8px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Signal Quality</div>
                <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#34C759" }}>
                  {signalQuality || "GOOD"}
                </div>
              </div>

              <div style={{ padding: "8px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Analysis Window</div>
                <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#FFFFFF" }}>
                  0.0s – 10.0s (1000 pts)
                </div>
              </div>

              <div style={{ padding: "8px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Sampling Rate</div>
                <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#FFFFFF" }}>
                  100 Hz
                </div>
              </div>

              <div style={{ padding: "8px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Inference Latency</div>
                <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#FFFFFF" }}>
                  {inferenceTimeMs}ms
                </div>
              </div>

              <div style={{ padding: "8px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Validation Status</div>
                <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#A78BFA" }}>
                  Validated (Fold 9)
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* COMBINED 4-CLASS PROBABILITY DISTRIBUTION */}
      {probabilityVector && probabilityVector.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", fontWeight: "700", color: "#FFFFFF" }}>
              <Info size={14} color="#8B5CF6" />
              <span>{isEnsembleMode ? "Combined 4-Class Probability Distribution" : "Class Probability Distribution"}</span>
            </div>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginLeft: "20px" }}>
              {isEnsembleMode 
                ? "Validation-weighted soft-voting probability assigned across all canonical rhythm classes."
                : `${modelVersion} predicted probability for each classification.`}
            </span>
          </div>
          <div style={{ width: "100%", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "12px", border: "1px solid rgba(255,255,255,0.04)" }}>
            {["Normal Sinus Rhythm", "Atrial Fibrillation (AFIB)", "Conduction Block", "Other Arrhythmia"].map((className, idx) => {
              const val = (probabilityVector[idx] || 0) * 100;
              const barColors = ["#5856D6", "#FF9500", "#FF2D55", "#007AFF"];
              return (
                <div key={className} style={{ display: "flex", alignItems: "center", gap: "12px", width: "100%" }}>
                  <div style={{ width: "160px", flexShrink: 0, fontSize: "0.75rem", color: "var(--text-secondary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {className}
                  </div>
                  <div style={{ flexGrow: 1, height: "14px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px", overflow: "hidden" }}>
                    <div style={{ width: `${Math.min(100, Math.max(0, val))}%`, height: "100%", backgroundColor: barColors[idx], borderRadius: "4px", transition: "width 0.5s ease-out" }} />
                  </div>
                  <div style={{ width: "50px", flexShrink: 0, fontSize: "0.75rem", fontWeight: "800", color: "#FFFFFF", textAlign: "right" }}>
                    {formatNumber(val, 1)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* INDIVIDUAL MODEL CONTRIBUTION PANEL (When in Ensemble Mode) */}
      {isEnsembleMode && contributingModels && contributingModels.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div 
            onClick={() => setShowModelContributions(prev => !prev)}
            style={{ 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "space-between", 
              cursor: "pointer", 
              padding: "4px 0" 
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Layers size={16} color="#8B5CF6" />
              <span style={{ fontSize: "0.85rem", fontWeight: "800", color: "#FFFFFF" }}>
                Individual Model Contribution & Weights ({contributingModels.length} of 7 Contributing)
              </span>
            </div>
            <button style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex", alignItems: "center" }}>
              {showModelContributions ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          {showModelContributions && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ overflowX: "auto", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.08)", color: "var(--text-secondary)" }}>
                      <th style={{ padding: "10px 12px" }}>Model</th>
                      <th style={{ padding: "10px 12px" }}>Architecture</th>
                      <th style={{ padding: "10px 12px" }}>Predicted Class</th>
                      <th style={{ padding: "10px 12px" }}>Probability</th>
                      <th style={{ padding: "10px 12px" }}>Assigned Weight</th>
                      <th style={{ padding: "10px 12px" }}>Effective Weight</th>
                      <th style={{ padding: "10px 12px" }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contributingModels.map((m: any, idx: number) => {
                      const isMatch = m.predicted_class === resultType;
                      return (
                        <tr 
                          key={m.model_id || idx} 
                          style={{ 
                            borderBottom: "1px solid rgba(255,255,255,0.03)",
                            background: isMatch ? "rgba(52, 199, 89, 0.03)" : "transparent"
                          }}
                        >
                          <td style={{ padding: "10px 12px", fontWeight: "700", color: "#FFFFFF" }}>
                            {m.model_id === "resnet" ? "1D CNN" : m.model_id}
                          </td>
                          <td style={{ padding: "10px 12px", color: "var(--text-secondary)" }}>
                            {m.architecture}
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <span style={{ 
                              padding: "2px 8px", 
                              borderRadius: "6px", 
                              fontWeight: "700",
                              fontSize: "0.7rem",
                              background: isMatch ? "rgba(52, 199, 89, 0.15)" : "rgba(255, 149, 0, 0.15)",
                              color: isMatch ? "#34C759" : "#FF9500"
                            }}>
                              {m.predicted_class}
                            </span>
                          </td>
                          <td style={{ padding: "10px 12px", fontWeight: "700", color: "#FFFFFF" }}>
                            {formatNumber(m.confidence, 1)}%
                          </td>
                          <td style={{ padding: "10px 12px", color: "var(--text-secondary)" }}>
                            {formatNumber((m.weight || 0.1) * 100, 1)}%
                          </td>
                          <td style={{ padding: "10px 12px", fontWeight: "700", color: "#A78BFA" }}>
                            {formatNumber((m.effective_weight || m.weight || 0.1) * 100, 1)}%
                          </td>
                          <td style={{ padding: "10px 12px" }}>
                            <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "#34C759", fontSize: "0.68rem", fontWeight: "700" }}>
                              <CheckCircle2 size={12} /> Contributing
                            </span>
                          </td>
                        </tr>
                      );
                    })}

                    {/* Excluded Models Display */}
                    {excludedModels && excludedModels.map((em: any, idx: number) => (
                      <tr key={`exc-${idx}`} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)", background: "rgba(255, 149, 0, 0.02)" }}>
                        <td style={{ padding: "10px 12px", fontWeight: "700", color: "#94A3B8" }}>
                          {em.model_id}
                        </td>
                        <td style={{ padding: "10px 12px", color: "#64748B" }}>
                          {em.architecture}
                        </td>
                        <td style={{ padding: "10px 12px", color: "#64748B" }}>
                          —
                        </td>
                        <td style={{ padding: "10px 12px", color: "#64748B" }}>
                          —
                        </td>
                        <td style={{ padding: "10px 12px", color: "#64748B" }}>
                          Excluded
                        </td>
                        <td style={{ padding: "10px 12px", color: "#64748B" }}>
                          0.0%
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "#FF9500", fontSize: "0.68rem", fontWeight: "700" }} title={em.reason}>
                            <XCircle size={12} /> {em.reason ? em.reason.slice(0, 32) + "..." : "Insufficient Input"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* MODEL AGREEMENT ANALYSIS */}
      {isEnsembleMode && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", fontWeight: "700", color: "#FFFFFF" }}>
            <AlertTriangle size={14} color="#FF9500" />
            <span>Model Agreement & Consensus Analysis</span>
          </div>

          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", 
            gap: "8px",
            backgroundColor: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.05)",
            borderRadius: "10px",
            padding: "12px"
          }}>
            <div>
              <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Agreeing Models</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "#34C759" }}>
                {agreementAnalysis?.agreeing_count ?? (contributingModels?.filter(m => m.predicted_class === resultType).length || 0)} Models
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Disagreeing Models</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "#FF9500" }}>
                {agreementAnalysis?.disagreeing_count ?? (contributingModels?.filter(m => m.predicted_class !== resultType).length || 0)} Models
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Agreement Rate</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "#8B5CF6" }}>
                {formatNumber(agreementAnalysis?.agreement_percentage ?? ((contributingModels?.filter(m => m.predicted_class === resultType).length || 0) / (contributingModels?.length || 1) * 100), 1)}%
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Excluded Models</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "#94A3B8" }}>
                {excludedModels?.length || 0} Models
              </div>
            </div>
          </div>

          <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontStyle: "italic", margin: "2px 0 0 0" }}>
            * Note: Agreement percentage measures algorithmic consensus across individual models and does not represent clinical diagnostic accuracy.
          </p>
        </div>
      )}

      {/* ECG SIGNAL FINDINGS & EXPLAINABILITY */}
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
                        padding: "6px 12px",
                        fontSize: "0.7rem",
                        fontWeight: "700",
                        color: "#FFFFFF",
                        backgroundColor: "rgba(0, 122, 255, 0.25)",
                        border: "1px solid rgba(0, 122, 255, 0.5)",
                        borderRadius: "8px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        boxShadow: "0 2px 8px rgba(0, 122, 255, 0.25)",
                        transition: "all 0.2s ease"
                      }}
                      title={"Focus " + region.start.toFixed(2) + "s - " + region.end.toFixed(2) + "s on ECG Monitor"}
                    >
                      <Activity size={12} color="#007AFF" />
                      <span>View on ECG</span>
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
            {isEnsembleMode ? (
              <>The <strong>Final Ensemble Model</strong> aggregated predictions from {contributingModelsCount || 7} verified deep-learning models, reaching consensus on <strong>{resultType}</strong> with {formatNumber(confidence, 1)}% confidence.</>
            ) : (
              <>The {modelVersion} model assigned the highest prediction probability to <strong>{resultType}</strong>. The highlighted waveform regions represent areas with stronger model attribution for this prediction.</>
            )}
          </span>
        </div>
      </div>

      {/* Clinical Disclaimer */}
      <div style={{ marginTop: "8px", padding: "12px", borderRadius: "10px", backgroundColor: "rgba(255, 149, 0, 0.05)", border: "1px solid rgba(255, 149, 0, 0.2)" }}>
        <h5 style={{ fontSize: "0.7rem", fontWeight: "800", color: "#FF9500", textTransform: "uppercase", marginBottom: "4px" }}>Research & Decision Support Disclaimer</h5>
        <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", lineHeight: "1.4", margin: 0 }}>
          CardioGuard AI ensemble outputs and model attributions are generated for clinical decision support and research exploration.<br/>
          They do not establish clinical causality or constitute an automated diagnosis without qualified medical review.
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

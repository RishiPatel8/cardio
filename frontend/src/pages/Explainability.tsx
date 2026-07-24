import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip as ChartTooltip, ReferenceLine, Cell 
} from "recharts";
import { 
  Cpu, Info, ShieldAlert 
} from "lucide-react";

interface FeatureContribution {
  feature_name: string;
  contribution_value: number;
  description: string;
}

interface ExplainabilityData {
  active_risk_score: number;
  confidence: number;
  model_version: string;
  explanation_text: string;
  contributions: FeatureContribution[];
}

const Explainability: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [data, setData] = useState<ExplainabilityData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchExplainability = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/explain`, { method: "GET", headers });
      if (res.ok) {
        const explData = await res.json();
        setData(explData);
      }
    } catch (err) {
      console.error("Failed to load explainability logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExplainability();
  }, [getUserToken, getAppCheckToken]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      
      {/* ⚠️ Regulatory Health Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 149, 0, 0.08)", border: "1px solid rgba(255, 149, 0, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="#FF9500" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Clinical Decision Support (Research Use):</span> CardioGuard AI risk logs represent research-oriented health analytics. They are not intended for clinical diagnostics or therapeutic decision-making.
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>AI Risk Factor Attribution</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Interpret how individual physiological variables, demographics, and clinical cofactors contribute to the overall risk assessment.
        </p>
      </div>

      {loading ? (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Calculating SHAP explainability variables...</span>
      ) : data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px" }} className="profile-grid">
          
          {/* Left panel - SHAP contributions bar chart */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            
            <div className="glass-panel" style={{ padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
                <Cpu size={20} color="var(--color-primary)" />
                <h3 style={{ fontSize: "1.05rem", fontWeight: "700" }}>SHAP Feature Contributions</h3>
              </div>

              {/* Recharts positive/negative bar graph */}
              <div style={{ width: "100%", height: "320px" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={data.contributions} 
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" stroke="var(--text-muted)" fontSize={10} domain={[-1, 1]} />
                    <YAxis type="category" dataKey="feature_name" stroke="#FFFFFF" fontSize={10} width={120} />
                    <ChartTooltip contentStyle={{ backgroundColor: "#1e1e24", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "11px", color: "#FFF" }} />
                    <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                    <Bar dataKey="contribution_value" name="Contribution Impact">
                      {data.contributions.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.contribution_value > 0 ? "var(--color-risk)" : "var(--color-normal)"} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "var(--text-muted)", marginTop: "12px" }}>
                <span>← Reduces Cardiovascular Risk (Wellness Tone)</span>
                <span>Elevates Cardiovascular Risk (Clinical Precursor) →</span>
              </div>
            </div>

            {/* Natural language summary explanation */}
            <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Info size={16} color="var(--color-secondary)" />
                <span style={{ fontSize: "0.85rem", fontWeight: "800", color: "#FFFFFF" }}>Natural Language Insights</span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: "1.5", margin: 0 }}>
                {data.explanation_text}
              </p>
            </div>

          </div>

          {/* Right panel - Score and model version */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            
            <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px", textAlign: "center" }}>
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Calculated Risk Index</h3>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <span style={{ fontSize: "2.2rem", fontWeight: "900", color: data.active_risk_score > 40 ? "var(--color-risk)" : "var(--color-normal)" }}>
                  {data.active_risk_score.toFixed(1)}%
                </span>
                <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Cardiovascular Risk Factors</span>
              </div>

              <div style={{ borderTop: "1px solid var(--border-glass)", paddingTop: "12px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Confidence</span>
                  <span style={{ fontSize: "0.85rem", fontWeight: "800", color: "#FFFFFF" }}>{data.confidence.toFixed(1)}%</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Model Version</span>
                  <span style={{ fontSize: "0.85rem", fontWeight: "800", color: "#FFFFFF" }}>{data.model_version}</span>
                </div>
              </div>
            </div>

            {/* Positive vs negative factors list */}
            <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <h3 style={{ fontSize: "0.85rem", fontWeight: "700" }}>Key Contributing Parameters</h3>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {data.contributions.slice(0, 4).map((c, idx) => (
                  <div key={idx} style={{ padding: "8px 12px", borderRadius: "6px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontSize: "0.7rem", fontWeight: "700" }}>{c.feature_name}</span>
                      <span style={{ fontSize: "0.58rem", color: "var(--text-muted)" }}>{c.description}</span>
                    </div>
                    <span style={{ fontSize: "0.75rem", fontWeight: "800", color: c.contribution_value > 0 ? "var(--color-risk)" : "var(--color-normal)" }}>
                      {c.contribution_value > 0 ? "+" : ""}{c.contribution_value.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>
      ) : (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Failed to construct SHAP explainers.</span>
      )}
    </div>
  );
};

export default Explainability;

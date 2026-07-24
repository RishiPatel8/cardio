import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  ShieldAlert, Cpu, RefreshCw, BarChart2 
} from "lucide-react";

interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  pr_auc: number;
  calibration_error: number;
}

interface ModelRegistryResponse {
  model_name: string;
  version: string;
  training_dataset: string;
  training_date: string;
  metrics: ModelMetrics;
  deployment_status: string;
  model_metadata: string;
}

const ModelRegistry: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [models, setModels] = useState<ModelRegistryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [rollbackTarget, setRollbackTarget] = useState("");
  const [rollingBack, setRollingBack] = useState(false);

  const fetchModels = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/models`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        setModels(data);
        // Default target is Standby model
        const standby = data.find((m: any) => m.deployment_status === "Standby");
        if (standby) setRollbackTarget(standby.version);
      }
    } catch (err) {
      console.error("Failed to load models list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, [getUserToken, getAppCheckToken]);

  const handleRollback = async () => {
    if (!rollbackTarget || rollingBack) return;
    setRollingBack(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/models/rollback`, {
        method: "POST",
        headers,
        body: JSON.stringify({ target_version: rollbackTarget })
      });

      if (res.ok) {
        alert(`Classifier target rolled back successfully to version: ${rollbackTarget}`);
        fetchModels();
      }
    } catch (err) {
      console.error("Rollback execution failed", err);
    } finally {
      setRollingBack(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      
      {/* ⚠️ Regulatory Health Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 149, 0, 0.08)", border: "1px solid rgba(255, 149, 0, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="#FF9500" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Clinical Decision Support Disclaimer:</span> Classifier calculations are intended as Clinical Decision Support (Research Use). They are not medical diagnostics and do not replace professional cardiologist evaluations.
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>AI Model Registry</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Track validation scores, calibration errors, and active deployments of machine learning classifier models.
        </p>
      </div>

      {loading ? (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loading registered models...</span>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px" }} className="profile-grid">
          
          {/* Models list */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {models.map((m) => (
              <div key={m.version} className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    <Cpu size={16} color="var(--color-primary)" />
                    <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "#FFFFFF" }}>{m.model_name}</h3>
                    <span style={{ fontSize: "0.65rem", padding: "2px 6px", borderRadius: "10px", backgroundColor: "rgba(255,255,255,0.05)", color: "var(--text-muted)" }}>{m.version}</span>
                  </div>
                  <span style={{ 
                    fontSize: "0.6rem", 
                    padding: "3px 8px", 
                    borderRadius: "12px", 
                    fontWeight: "700",
                    backgroundColor: m.deployment_status === "Active" ? "rgba(52,199,89,0.12)" : (m.deployment_status === "Standby" ? "rgba(255,149,0,0.12)" : "rgba(255,255,255,0.05)"),
                    color: m.deployment_status === "Active" ? "var(--color-normal)" : (m.deployment_status === "Standby" ? "#FF9500" : "var(--text-muted)")
                  }}>
                    {m.deployment_status}
                  </span>
                </div>

                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", margin: 0 }}>
                  {m.model_metadata} Trained on {m.training_dataset} ({m.training_date}).
                </p>

                {/* Metrics grids */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px" }}>
                  {[
                    { label: "Accuracy", val: (m.metrics.accuracy * 100).toFixed(1) + "%" },
                    { label: "F1 Score", val: m.metrics.f1_score.toFixed(3) },
                    { label: "ROC AUC", val: m.metrics.roc_auc.toFixed(4) },
                    { label: "PR AUC", val: m.metrics.pr_auc.toFixed(4) }
                  ].map((met, idx) => (
                    <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "2px", textAlign: "center" }}>
                      <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>{met.label}</span>
                      <span style={{ fontSize: "0.75rem", fontWeight: "800", color: "#FFFFFF" }}>{met.val}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Model rollbacks control */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px", height: "fit-content" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <RefreshCw size={16} color="var(--color-secondary)" />
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Deployment Rollback</h3>
            </div>

            <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
              Change the active production classifier. This updates risk scores calculations across all user profiles instantly.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Target Model Version</label>
              <select 
                value={rollbackTarget} 
                onChange={(e) => setRollbackTarget(e.target.value)}
                style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
              >
                {models.map((m) => (
                  <option key={m.version} value={m.version}>
                    {m.model_name} ({m.version})
                  </option>
                ))}
              </select>
            </div>

            <button 
              onClick={handleRollback}
              disabled={rollingBack || !rollbackTarget}
              className="btn-secondary" 
              style={{ width: "100%", justifyContent: "center", padding: "10px", fontSize: "0.75rem", fontWeight: "700", color: "var(--color-secondary)", borderColor: "rgba(10,186,181,0.2)" }}
            >
              <BarChart2 size={14} />
              {rollingBack ? "Deploying..." : "Rollback to Selected Model"}
            </button>
          </div>

        </div>
      )}
    </div>
  );
};

export default ModelRegistry;

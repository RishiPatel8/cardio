import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  Database, ShieldAlert, Upload 
} from "lucide-react";

interface DatasetSplit {
  train_pct: number;
  val_pct: number;
  test_pct: number;
}

interface LabelDistribution {
  class_label: string;
  count: number;
  percentage: number;
}

interface DatasetStats {
  dataset_name: string;
  version: string;
  patient_counts: number;
  signal_counts: number;
  sampling_frequency_hz: number;
  splits: DatasetSplit;
  class_distribution: LabelDistribution[];
}

const DatasetManager: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [datasets, setDatasets] = useState<DatasetStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);

  const fetchDatasets = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/datasets`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
      }
    } catch (err) {
      console.error("Failed to load dataset statistics", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [getUserToken, getAppCheckToken]);

  const activeDataset = datasets.length > 0 ? datasets[activeTab] : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      
      {/* ⚠️ Regulatory Health Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 149, 0, 0.08)", border: "1px solid rgba(255, 149, 0, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="#FF9500" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Research Database Disclaimer:</span> Dataset management controls support research-oriented health analytics. They are intended for model training evaluations and do not replace professional cardiology diagnostic procedures.
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Dataset Management</h2>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            Review sample signal distribution, sampling frequencies, validation splits, and class balances across research databases.
          </p>
        </div>
        <button onClick={() => alert("Upload dataset files (PhysioNet format).")} className="btn-primary" style={{ padding: "10px 16px", fontSize: "0.8rem" }}>
          <Upload size={14} /> Upload Dataset CSV
        </button>
      </div>

      {loading ? (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loading database statistics...</span>
      ) : activeDataset ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "24px" }} className="profile-grid">
          
          {/* Left column: Dataset tabs list */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {datasets.map((d, index) => (
              <button 
                key={d.dataset_name}
                onClick={() => setActiveTab(index)}
                className={`glass-panel btn-secondary`}
                style={{ 
                  textAlign: "left",
                  padding: "16px", 
                  borderRadius: "10px", 
                  backgroundColor: activeTab === index ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.01)",
                  border: `1px solid ${activeTab === index ? "var(--color-primary)" : "var(--border-glass)"}`,
                  color: "#FFFFFF",
                  cursor: "pointer",
                  display: "flex",
                  gap: "10px",
                  alignItems: "center"
                }}
              >
                <Database size={16} color={activeTab === index ? "var(--color-primary)" : "var(--text-muted)"} />
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.78rem", fontWeight: "700" }}>{d.dataset_name}</span>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", marginTop: "2px" }}>Version {d.version}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Right column: active dataset details */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: "800", color: "#FFFFFF" }}>{activeDataset.dataset_name}</h3>
              <span style={{ fontSize: "0.65rem", padding: "2px 6px", borderRadius: "8px", backgroundColor: "rgba(255,255,255,0.05)", color: "var(--text-secondary)" }}>{activeDataset.sampling_frequency_hz} Hz</span>
            </div>

            {/* Basic counts */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <span style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Patient Count</span>
                <span style={{ fontSize: "1.1rem", fontWeight: "800", color: "#FFFFFF" }}>{activeDataset.patient_counts.toLocaleString()}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <span style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>ECG Signal Records</span>
                <span style={{ fontSize: "1.1rem", fontWeight: "800", color: "#FFFFFF" }}>{activeDataset.signal_counts.toLocaleString()}</span>
              </div>
            </div>

            {/* Validation Split ratios */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "16px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "700" }}>Validation Split Allocation:</span>
              
              <div style={{ display: "flex", height: "18px", borderRadius: "9px", overflow: "hidden", backgroundColor: "rgba(255,255,255,0.05)" }}>
                <div style={{ width: `${activeDataset.splits.train_pct}%`, backgroundColor: "var(--color-primary)" }} title="Train Split" />
                <div style={{ width: `${activeDataset.splits.val_pct}%`, backgroundColor: "#FF9500" }} title="Validation Split" />
                <div style={{ width: `${activeDataset.splits.test_pct}%`, backgroundColor: "#007AFF" }} title="Test Split" />
              </div>
              
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "var(--text-muted)" }}>
                <span>• Train: {activeDataset.splits.train_pct}%</span>
                <span>• Val: {activeDataset.splits.val_pct}%</span>
                <span>• Test: {activeDataset.splits.test_pct}%</span>
              </div>
            </div>

            {/* Class distribution balances */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "700" }}>Label Distribution & Class Balance:</span>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {activeDataset.class_distribution.map((c, idx) => (
                  <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.68rem" }}>
                      <span style={{ color: "#FFFFFF" }}>{c.class_label}</span>
                      <span style={{ color: "var(--text-muted)" }}>{c.count.toLocaleString()} ({c.percentage}%)</span>
                    </div>
                    <div style={{ width: "100%", height: "6px", borderRadius: "3px", backgroundColor: "rgba(255,255,255,0.03)" }}>
                      <div style={{ width: `${c.percentage}%`, height: "100%", borderRadius: "3px", backgroundColor: "var(--color-primary)" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>
      ) : (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Failed to retrieve dataset metrics.</span>
      )}
    </div>
  );
};

export default DatasetManager;

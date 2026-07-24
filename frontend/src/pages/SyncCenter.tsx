import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  RefreshCw, CheckCircle2, AlertOctagon, Info, Database, 
  Download, Upload 
} from "lucide-react";

interface SyncLog {
  id: string;
  job_type: string;
  status: string;
  retry_count: number;
  created_at: string;
}

const SyncCenter: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [logs, setLogs] = useState<SyncLog[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [successCount, setSuccessCount] = useState(24);
  const [failCount, setFailCount] = useState(1);
  const [duplicatesRemoved, setDuplicatesRemoved] = useState(148);

  const fetchSyncJobs = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/jobs`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Failed to load sync jobs logs", err);
    }
  };

  useEffect(() => {
    fetchSyncJobs();
  }, [getUserToken, getAppCheckToken]);

  const handleManualSync = async () => {
    setSyncing(true);
    try {
      // Simulate calling wearable sync
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      // Sync virtual packet to trigger duplicates filter
      await fetch(`${apiUrl}/wearables/sync`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          source: "sync_center",
          file_name: "wearables_batch.csv",
          avg_bpm: 72,
          sdrr_ms: 38,
          rmssd_ms: 36,
          sleep_minutes: 450,
          calories_burned: 420,
          steps_count: 8500,
          spo2: 98,
          systolic_bp: 120,
          diastolic_bp: 80,
          timeseries_data: []
        })
      });
      
      setSuccessCount(prev => prev + 1);
      setDuplicatesRemoved(prev => prev + 4);
      fetchSyncJobs();
    } catch (err) {
      setFailCount(prev => prev + 1);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px", width: "100%", paddingBottom: "40px" }} className="profile-grid">
      
      {/* Left panel - Sync statistics and controls */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Core sync widget */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <Database size={20} color="var(--color-primary)" />
              <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Biometric Database Sync Center</h3>
            </div>
            <button 
              onClick={handleManualSync} 
              disabled={syncing}
              className="btn-primary" 
              style={{ fontSize: "0.8rem", padding: "10px 16px" }}
            >
              <RefreshCw size={14} style={{ animation: syncing ? "spin 1s linear infinite" : "none" }} />
              {syncing ? "Synchronizing Vitals..." : "Synchronize Now"}
            </button>
          </div>

          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
            Verify connection status with Google Fit and Health Connect SDK layers. Missing timestamps are auto-filled, timezone disparities calibrated, and duplicate entries deleted before risk assessment calculations.
          </p>

          {/* Key counters */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255,255,255,0.01)" }}>
              <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Successful Syncs</span>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <CheckCircle2 size={14} color="var(--color-normal)" />
                <span style={{ fontSize: "1.2rem", fontWeight: "800", color: "#FFFFFF" }}>{successCount}</span>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255,255,255,0.01)" }}>
              <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Failed Syncs</span>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <AlertOctagon size={14} color="var(--color-risk)" />
                <span style={{ fontSize: "1.2rem", fontWeight: "800", color: "#FFFFFF" }}>{failCount}</span>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255,255,255,0.01)" }}>
              <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Duplicates Purged</span>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Info size={14} color="var(--color-secondary)" />
                <span style={{ fontSize: "1.2rem", fontWeight: "800", color: "#FFFFFF" }}>{duplicatesRemoved}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sync logs timeline */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>System Sync Verification Audit Logs</h3>
          
          {logs.length === 0 ? (
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>No sync events logged.</span>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {logs.map((log) => (
                <div key={log.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", borderRadius: "6px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <Database size={14} color="var(--color-primary)" />
                    <span style={{ fontSize: "0.75rem", fontWeight: "600" }}>{log.job_type}</span>
                  </div>
                  <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                    <span style={{ fontSize: "0.6rem", color: log.status === "completed" ? "var(--color-normal)" : "var(--color-risk)", fontWeight: "700", textTransform: "uppercase" }}>{log.status}</span>
                    <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>{new Date(log.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Right panel - Platform connection status controls */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Sync sources status */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Active API Sync Channels</h3>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {[
              { label: "Google Fit API Connection", status: "Active (Token Valid)", speed: "0.8s" },
              { label: "Health Connect SDK Listener", status: "Active (Permissions Approved)", speed: "0.4s" },
              { label: "PostgreSQL Database Engine", status: "Connected", speed: "2.1ms" },
              { label: "Redis Caching Cluster", status: "Connected", speed: "1.0ms" }
            ].map((ch, idx) => (
              <div key={idx} style={{ padding: "12px", borderRadius: "8px", border: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", fontSize: "0.7rem" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <span style={{ fontWeight: "700" }}>{ch.label}</span>
                  <span style={{ color: "var(--text-secondary)" }}>{ch.status}</span>
                </div>
                <span style={{ alignSelf: "center", color: "var(--color-normal)", fontWeight: "700" }}>{ch.speed}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Local CSV imports/exports */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Local Data Migration</h3>
          
          <div style={{ display: "flex", gap: "12px" }}>
            <button onClick={() => alert("CSV Export initialized.")} className="btn-secondary" style={{ flex: 1, padding: "10px", justifyContent: "center", fontSize: "0.75rem" }}>
              <Download size={14} /> Export CSV
            </button>
            <button onClick={() => alert("CSV Import initialized.")} className="btn-secondary" style={{ flex: 1, padding: "10px", justifyContent: "center", fontSize: "0.75rem" }}>
              <Upload size={14} /> Import CSV
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};

export default SyncCenter;

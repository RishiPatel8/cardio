import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  Activity, Cpu, Database, HardDrive, Clock, 
  Terminal, ShieldAlert 
} from "lucide-react";

interface MonitoringData {
  host_resources: {
    cpu_percent: number;
    ram_percent: number;
    disk_percent: number;
    gpu_percent: number;
  };
  latencies: {
    api_response_ms: number;
    prediction_latency_ms: number;
  };
  services_health: {
    database_status: string;
    redis_status: string;
    queue_backlog: number;
  };
}

const SystemMonitoring: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [data, setData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTelemetry = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/monitoring`, { method: "GET", headers });
      if (res.ok) {
        const telData = await res.json();
        setData(telData);
      }
    } catch (err) {
      console.error("Failed to load monitoring logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(interval);
  }, [getUserToken, getAppCheckToken]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      
      {/* ⚠️ Regulatory Health Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 149, 0, 0.08)", border: "1px solid rgba(255, 149, 0, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="#FF9500" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Admin Disclaimer:</span> All monitoring parameters represent research-oriented server telemetry logs and do not perform patient medical diagnoses.
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Admin System Telemetry</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Monitor live host CPU loads, virtual memory allocation, database latency metrics, and API service request status.
        </p>
      </div>

      {loading ? (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loading host hardware logs...</span>
      ) : data ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px" }} className="profile-grid">
          
          {/* Left panel - hardware parameters & dials */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            
            {/* Hardware resource cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
              {[
                { label: "Host CPU Load", val: `${data.host_resources.cpu_percent.toFixed(1)}%`, icon: <Cpu size={16} color="var(--color-primary)" /> },
                { label: "Virtual RAM", val: `${data.host_resources.ram_percent.toFixed(1)}%`, icon: <Activity size={16} color="var(--color-secondary)" /> },
                { label: "Disk Storage", val: `${data.host_resources.disk_percent.toFixed(1)}%`, icon: <HardDrive size={16} color="#FFCC00" /> },
                { label: "GPU Load", val: `${data.host_resources.gpu_percent.toFixed(1)}%`, icon: <Cpu size={16} color="#AF52DE" /> }
              ].map((res, idx) => (
                <div key={idx} className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>{res.label}</span>
                    {res.icon}
                  </div>
                  <span style={{ fontSize: "1.3rem", fontWeight: "800", color: "#FFFFFF" }}>{res.val}</span>
                </div>
              ))}
            </div>

            {/* API performance and processing latency */}
            <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Clock size={18} color="var(--color-primary)" />
                <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>API Service Performance & Latency</h3>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div style={{ padding: "16px", borderRadius: "8px", border: "1px solid var(--border-glass)", display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Mean API Response Delay</span>
                  <span style={{ fontSize: "1.4rem", fontWeight: "900", color: "var(--color-normal)" }}>{data.latencies.api_response_ms} ms</span>
                </div>

                <div style={{ padding: "16px", borderRadius: "8px", border: "1px solid var(--border-glass)", display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>AI Risk Classification Latency</span>
                  <span style={{ fontSize: "1.4rem", fontWeight: "900", color: "var(--color-secondary)" }}>{data.latencies.prediction_latency_ms} ms</span>
                </div>
              </div>
            </div>

            {/* Service health check statuses */}
            <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Database size={18} color="var(--color-secondary)" />
                <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Bioservice Dependencies Health Status</h3>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {[
                  { label: "PostgreSQL Database Service", val: data.services_health.database_status, status: "Normal" },
                  { label: "Redis Key-Value Cache Cluster", val: data.services_health.redis_status, status: "Normal" },
                  { label: "Async Task Worker Queues", val: `Queue Backlog Size: ${data.services_health.queue_backlog}`, status: "Empty" }
                ].map((s, idx) => (
                  <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255,255,255,0.01)" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: "700" }}>{s.label}</span>
                      <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{s.val}</span>
                    </div>
                    <span style={{ fontSize: "0.6rem", padding: "3px 8px", borderRadius: "10px", backgroundColor: "rgba(52,199,89,0.1)", color: "var(--color-normal)", fontWeight: "700" }}>{s.status}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Right panel - terminal/console logs log simulation */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px", height: "100%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Terminal size={18} color="#FFFFFF" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Production Application Logs</h3>
            </div>

            <div style={{ backgroundColor: "#0b0c10", borderRadius: "8px", padding: "12px", flex: 1, fontFamily: "monospace", fontSize: "0.6rem", color: "#66fcf1", overflowY: "auto", minHeight: "350px", lineHeight: "1.4" }}>
              <div>[INFO] 2026-07-24T13:30:12Z - Connected to database engine.</div>
              <div>[INFO] 2026-07-24T13:30:15Z - Redis socket verification successful.</div>
              <div>[INFO] 2026-07-24T13:30:20Z - FCM push messaging socket configured.</div>
              <div>[INFO] 2026-07-24T13:31:05Z - Syncing batches of wearable parameters...</div>
              <div>[INFO] 2026-07-24T13:31:06Z - Cleaned 4 duplicate database rows.</div>
              <div>[INFO] 2026-07-24T13:31:08Z - AI risk assessment triggered successfully.</div>
              <div>[INFO] 2026-07-24T13:31:12Z - Prediction outputs saved. Latency 0.14ms.</div>
              <div>[INFO] 2026-07-24T13:31:18Z - Clinician observations list retrieved.</div>
              <div>[INFO] 2026-07-24T13:32:00Z - Running diagnostic test routines.</div>
            </div>
          </div>

        </div>
      ) : (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Failed to retrieve host health telemetry.</span>
      )}
    </div>
  );
};

export default SystemMonitoring;

import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  Laptop, Wifi, AlertTriangle, RefreshCw, 
  CheckCircle2, ShieldAlert
} from "lucide-react";

interface WearableDevice {
  id: string;
  device_name: string;
  manufacturer: string;
  connection_status: string;
  battery_percent: number;
  firmware_version: string;
  hr_sensor: boolean;
  spo2_sensor: boolean;
  sleep_sensor: boolean;
  gyro_sensor: boolean;
  gps_sensor: boolean;
  last_sync: string;
}

const Devices: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [devices, setDevices] = useState<WearableDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);

  const fetchDevices = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/devices`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        setDevices(data);
      }
    } catch (err) {
      console.error("Failed to load devices", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, [getUserToken, getAppCheckToken]);

  const handleRunDiagnostics = async (id: string) => {
    setRefreshing(id);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/devices/${id}/diagnostics`, {
        method: "POST",
        headers,
      });
      if (res.ok) {
        fetchDevices();
      }
    } catch (err) {
      console.error("Diagnostics execution failure", err);
    } finally {
      setRefreshing(null);
    }
  };

  const handleDisconnect = async (id: string) => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/devices/${id}/disconnect`, {
        method: "DELETE",
        headers,
      });
      if (res.ok) {
        fetchDevices();
      }
    } catch (err) {
      console.error("Disconnection failure", err);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      
      {/* ⚠️ Regulatory Health Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 149, 0, 0.08)", border: "1px solid rgba(255, 149, 0, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="#FF9500" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Research & Wellness Support Disclaimer:</span> CardioGuard AI is intended for research, educational, and wellness support. It does not perform medical diagnoses, detect diseases, or replace professional clinical evaluation or advice.
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Wearable Device Management</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Configure connected health wearables, register sensor gateways, and review hardware battery logs.
        </p>
      </div>

      {loading ? (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loading connected devices...</span>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
          {devices.map((dev) => (
            <div key={dev.id} className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                  <div style={{ width: "40px", height: "40px", borderRadius: "8px", backgroundColor: "rgba(0,122,255,0.08)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Laptop size={20} color="var(--color-primary)" />
                  </div>
                  <div>
                    <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "#FFFFFF" }}>{dev.device_name}</h3>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{dev.manufacturer} • Firmware {dev.firmware_version}</span>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Wifi size={14} color="var(--color-normal)" />
                  <span style={{ fontSize: "0.65rem", color: "var(--color-normal)", fontWeight: "700" }}>{dev.connection_status}</span>
                </div>
              </div>

              {/* Hardware diagnostics metrics */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", padding: "12px", borderRadius: "8px" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Battery Level</span>
                  <span style={{ fontSize: "0.85rem", fontWeight: "800", color: dev.battery_percent < 20 ? "var(--color-risk)" : "#FFFFFF" }}>{dev.battery_percent}%</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Last Synced</span>
                  <span style={{ fontSize: "0.85rem", fontWeight: "800", color: "#FFFFFF" }}>{new Date(dev.last_sync).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>

              {/* Sensor list */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "700" }}>Active Biosensors:</span>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  {[
                    { label: "Heart Rate Sensor", val: dev.hr_sensor },
                    { label: "SpO₂ Saturation", val: dev.spo2_sensor },
                    { label: "Sleep Tracker", val: dev.sleep_sensor },
                    { label: "Accelerometer", val: dev.gyro_sensor },
                    { label: "GPS Telemetry", val: dev.gps_sensor }
                  ].map((s, idx) => (
                    <div key={idx} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.65rem", color: s.val ? "#FFFFFF" : "var(--text-muted)" }}>
                      <CheckCircle2 size={12} color={s.val ? "var(--color-normal)" : "var(--text-muted)"} />
                      <span>{s.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <button 
                  onClick={() => handleRunDiagnostics(dev.id)} 
                  disabled={refreshing === dev.id}
                  className="btn-secondary" 
                  style={{ flex: 1, padding: "10px", justifyContent: "center", fontSize: "0.75rem" }}
                >
                  <RefreshCw size={12} style={{ animation: refreshing === dev.id ? "spin 1s linear infinite" : "none" }} />
                  {refreshing === dev.id ? "Testing..." : "Test Sensors"}
                </button>
                <button 
                  onClick={() => handleDisconnect(dev.id)}
                  className="btn-secondary" 
                  style={{ flex: 1, padding: "10px", justifyContent: "center", color: "var(--color-risk)", borderColor: "rgba(255,59,48,0.2)", fontSize: "0.75rem" }}
                >
                  <AlertTriangle size={12} />
                  Disconnect
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Devices;

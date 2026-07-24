import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  ToggleLeft, ToggleRight, FileText, Trash2, 
  Download, AlertTriangle, ShieldCheck 
} from "lucide-react";

interface PrivacyConsent {
  research_consent: boolean;
  clinical_sharing: boolean;
  doctor_access: boolean;
  cloud_backup: boolean;
  anonymous_analytics: boolean;
  location_permission: boolean;
  notification_permission: boolean;
}

const Privacy: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [consent, setConsent] = useState<PrivacyConsent>({
    research_consent: false,
    clinical_sharing: false,
    doctor_access: false,
    cloud_backup: true,
    anonymous_analytics: true,
    location_permission: false,
    notification_permission: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchConsent = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/privacy/consent`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        setConsent(data);
      }
    } catch (err) {
      console.error("Failed to load privacy consent logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsent();
  }, [getUserToken, getAppCheckToken]);

  const handleToggle = async (key: keyof PrivacyConsent) => {
    const updatedConsent = { ...consent, [key]: !consent[key] };
    setConsent(updatedConsent);
    setSaving(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/privacy/consent`, {
        method: "POST",
        headers,
        body: JSON.stringify(updatedConsent)
      });
      if (res.ok) {
        const data = await res.json();
        setConsent(data);
      }
    } catch (err) {
      console.error("Consent save failure", err);
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/privacy/export`, { method: "POST", headers });
      if (res.ok) {
        const data = await res.json();
        alert(`GDPR Data Export successful! Audit ID: ${data.audit_id}\nDownload link: ${data.download_url}`);
      }
    } catch (err) {
      alert("Failed to export privacy data.");
    }
  };

  const handleDeleteAccount = async () => {
    if (!confirm("Are you absolutely sure you want to request account deletion under GDPR Right to be Forgotten? All health logs, profiles, and prediction history will be permanently deleted and cannot be undone.")) return;
    
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/privacy/delete-account`, { method: "POST", headers });
      if (res.ok) {
        alert("Account purged successfully. Logging out.");
        window.location.reload();
      }
    } catch (err) {
      alert("Purge operation failed.");
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px", width: "100%", paddingBottom: "40px" }} className="profile-grid">
      
      {/* Left panel - GDPR Toggles */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
            <ShieldCheck size={20} color="var(--color-primary)" />
            <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>GDPR Consent & Privacy Controls</h3>
          </div>

          {loading ? (
            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Loading privacy configurations...</span>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {[
                { key: "research_consent", label: "De-identified Research Consent", desc: "Allow CardioGuard clinical researchers to use my de-identified HRV/ECG logs in medical studies." },
                { key: "clinical_sharing", label: "Clinical Data Sharing", desc: "Permit hospital electronic medical records (EMR) query integrations." },
                { key: "doctor_access", label: "Real-time Doctor Portal Access", desc: "Allow my primary cardiologist to review live vitals sync updates and prediction trends." },
                { key: "cloud_backup", label: "Encrypted Cloud Backups", desc: "Backup synchronized data to PostgreSQL databases." },
                { key: "anonymous_analytics", label: "Anonymous Application Analytics", desc: "Log crash reporting metrics and performance latency." },
                { key: "location_permission", label: "Location Services (GPS)", desc: "Enable proximity coordinates tracking for cardiac emergency triggers." },
                { key: "notification_permission", label: "Arrhythmia Alerting Notifications", desc: "Send immediate alarms during high-risk cardiac warning thresholds." }
              ].map((item, idx) => (
                <div 
                  key={idx}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: "12px", borderBottom: idx < 6 ? "1px solid var(--border-glass)" : "none" }}
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", maxWidth: "80%" }}>
                    <span style={{ fontSize: "0.8rem", fontWeight: "700" }}>{item.label}</span>
                    <span style={{ fontSize: "0.68rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>{item.desc}</span>
                  </div>
                  <button 
                    onClick={() => handleToggle(item.key as keyof PrivacyConsent)}
                    disabled={saving}
                    style={{ background: "none", border: "none", cursor: "pointer", color: consent[item.key as keyof PrivacyConsent] ? "var(--color-primary)" : "var(--text-muted)" }}
                  >
                    {consent[item.key as keyof PrivacyConsent] ? <ToggleRight size={32} /> : <ToggleLeft size={32} />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Right panel - GDPR Purge controls */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
            <FileText size={18} color="var(--color-secondary)" />
            <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>GDPR Actions Workspace</h3>
          </div>
          
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
            Export or completely purge all database telemetry in alignment with local Right to be Forgotten policies.
          </p>

          <button 
            onClick={handleExportData}
            className="btn-secondary" 
            style={{ width: "100%", justifyContent: "center", padding: "12px", fontSize: "0.8rem" }}
          >
            <Download size={14} /> Export My Data File
          </button>

          <button 
            onClick={handleDeleteAccount}
            className="btn-secondary" 
            style={{ width: "100%", justifyContent: "center", borderColor: "rgba(255,59,48,0.2)", color: "var(--color-risk)", padding: "12px", fontSize: "0.8rem" }}
          >
            <Trash2 size={14} /> Purge My Profile & Data
          </button>
        </div>

        {/* Clinical Disclaimer reminder */}
        <div className="glass-panel" style={{ display: "flex", gap: "12px", border: "1px solid rgba(255, 149, 0, 0.2)", background: "rgba(255, 149, 0, 0.02)" }}>
          <AlertTriangle size={18} color="#FF9500" style={{ flexShrink: 0 }} />
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#FFFFFF" }}>Patient Disclaimer</span>
            <p style={{ fontSize: "0.68rem", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              All diagnostics parameters compiled represent clinical decision support metrics for research applications. They do not replace formal hospital ECG assessments.
            </p>
          </div>
        </div>

      </div>

    </div>
  );
};

export default Privacy;

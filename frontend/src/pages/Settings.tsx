import React, { useState } from "react";
import { 
  ShieldCheck, Save, Globe, Eye, Server, 
  HelpCircle, ShieldAlert 
} from "lucide-react";

const Settings: React.FC = () => {
  // Expanded settings states
  const [theme, setTheme] = useState("dark");
  const [language, setLanguage] = useState("en");
  const [timezone, setTimezone] = useState("UTC");
  const [measurementSystem, setMeasurementSystem] = useState("metric");
  
  const [heightUnit, setHeightUnit] = useState("cm");
  const [weightUnit, setWeightUnit] = useState("kg");
  const [bpUnit, setBpUnit] = useState("mmHg");
  
  const [syncFreq, setSyncFreq] = useState("60m");
  const [dataRetention, setDataRetention] = useState("12m");
  const [devMode, setDevMode] = useState(false);
  const [offlineMode, setOfflineMode] = useState(false);

  const [alertsConfig, setAlertsConfig] = useState({
    highHr: true,
    afRisk: true,
    autoSync: false
  });

  const handleSave = () => {
    alert("Preferences and configurations updated successfully in production settings.");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      
      {/* ⚠️ Regulatory Health Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 149, 0, 0.08)", border: "1px solid rgba(255, 149, 0, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="#FF9500" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Patient Disclaimer:</span> Configurations modified here adjust diagnostic alerts. These assessments represent research-oriented health risk parameters and are not clinical diagnoses.
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Diagnostic & System Settings</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Calibrate security modules, synchronization frequencies, telemetry units, and clinical alert boundaries.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px" }} className="profile-grid">
        
        {/* Left column: Expanded settings forms */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* General customization options */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Globe size={18} color="var(--color-primary)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Localization & Theme Preference</h3>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>System Theme</label>
                <select 
                  value={theme} 
                  onChange={(e) => setTheme(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="dark">Dark Theme (Glassmorphism)</option>
                  <option value="light">Light Theme (Minimalist)</option>
                  <option value="system">System Default</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>System Language</label>
                <select 
                  value={language} 
                  onChange={(e) => setLanguage(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="en">English (US)</option>
                  <option value="es">Español (ES)</option>
                  <option value="de">Deutsch (DE)</option>
                  <option value="fr">Français (FR)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>System Timezone</label>
                <select 
                  value={timezone} 
                  onChange={(e) => setTimezone(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="UTC">Coordinated Universal Time (UTC)</option>
                  <option value="EST">Eastern Standard Time (EST)</option>
                  <option value="PST">Pacific Standard Time (PST)</option>
                  <option value="GMT">Greenwich Mean Time (GMT)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Measurement System</label>
                <select 
                  value={measurementSystem} 
                  onChange={(e) => setMeasurementSystem(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="metric">Metric System (cm, kg)</option>
                  <option value="imperial">Imperial System (inches, lbs)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Biosensors units options */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Eye size={18} color="var(--color-secondary)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Biometric Unit Configurations</h3>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Height Units</label>
                <select 
                  value={heightUnit} 
                  onChange={(e) => setHeightUnit(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="cm">Centimeters (cm)</option>
                  <option value="inches">Inches (in)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Weight Units</label>
                <select 
                  value={weightUnit} 
                  onChange={(e) => setWeightUnit(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="kg">Kilograms (kg)</option>
                  <option value="lbs">Pounds (lbs)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Blood Pressure Units</label>
                <select 
                  value={bpUnit} 
                  onChange={(e) => setBpUnit(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="mmHg">Millimeters of Mercury (mmHg)</option>
                  <option value="kPa">Kilopascals (kPa)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Sync frequency and data retention */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Server size={18} color="#FF9500" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Data Storage & Sync Intervals</h3>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Auto Sync Interval</label>
                <select 
                  value={syncFreq} 
                  onChange={(e) => setSyncFreq(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="15m">Every 15 minutes</option>
                  <option value="30m">Every 30 minutes</option>
                  <option value="60m">Every 60 minutes</option>
                  <option value="12h">Every 12 hours</option>
                  <option value="24h">Daily (Every 24 hours)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Telemetry Data Retention</label>
                <select 
                  value={dataRetention} 
                  onChange={(e) => setDataRetention(e.target.value)}
                  style={{ padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value="1m">1 Month (Rolling Purge)</option>
                  <option value="6m">6 Months</option>
                  <option value="12m">12 Months (1 Year)</option>
                  <option value="infinite">Keep All Logs Permanently</option>
                </select>
              </div>
            </div>
          </div>

        </div>

        {/* Right column: Toggles and save actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Diagnostic warnings and alerts */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <ShieldCheck size={18} color="var(--color-normal)" />
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Diagnostic Warning Alerts</h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {[
                { key: "highHr", label: "Resting Tachycardia Alerts", desc: "Alarm if RHR exceeds 120 bpm." },
                { key: "afRisk", label: "High Confidence Warning", desc: "Notify when AF risk score exceeds 85%." },
                { key: "autoSync", label: "Auto Sync Trigger logs", desc: "Send status notifications on database sync success." }
              ].map((al) => (
                <div key={al.key} style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", fontSize: "0.68rem" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px", maxWidth: "80%" }}>
                    <span style={{ fontWeight: "700", color: "#FFFFFF" }}>{al.label}</span>
                    <span style={{ color: "var(--text-secondary)" }}>{al.desc}</span>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={alertsConfig[al.key as keyof typeof alertsConfig]}
                    onChange={() => setAlertsConfig({ ...alertsConfig, [al.key]: !alertsConfig[al.key as keyof typeof alertsConfig] })}
                    style={{ marginTop: "4px" }}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* DevMode options */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <HelpCircle size={18} color="var(--color-primary)" />
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>System & Developer Settings</h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "0.68rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Offline Storage Cache</span>
                  <span style={{ color: "var(--text-secondary)" }}>Cache telemetry locally when offline.</span>
                </div>
                <input 
                  type="checkbox" 
                  checked={offlineMode}
                  onChange={() => setOfflineMode(!offlineMode)}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Developer Mode logs</span>
                  <span style={{ color: "var(--text-secondary)" }}>Unlock research model debugging consoles.</span>
                </div>
                <input 
                  type="checkbox" 
                  checked={devMode}
                  onChange={() => setDevMode(!devMode)}
                />
              </div>
            </div>
          </div>

          {/* Submit Actions */}
          <button 
            onClick={handleSave} 
            className="btn-primary" 
            style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: "0.9rem", fontWeight: "700" }}
          >
            <Save size={16} /> Save Configurations
          </button>

        </div>

      </div>

    </div>
  );
};

export default Settings;

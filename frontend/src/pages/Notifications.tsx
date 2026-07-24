import React from "react";
import { ShieldAlert, CheckCircle, Info } from "lucide-react";

const Notifications: React.FC = () => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Rhythm Warnings & Alerts</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Manage your system logs, synchronization reports, and critical arrhythmia alerts.
        </p>
      </div>

      <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>System Notification Log</h3>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {[
            { id: "1", type: "risk", msg: "Atrial Fibrillation Risk warning generated for dataset upload.", date: "July 24, 2026 • 12:44 PM", icon: ShieldAlert, color: "var(--color-risk)" },
            { id: "2", type: "success", msg: "Google Fit wear telemetry sync completed successfully.", date: "July 24, 2026 • 11:30 AM", icon: CheckCircle, color: "var(--color-normal)" },
            { id: "3", type: "info", msg: "New firmware update available for Apple Watch Ultra integration.", date: "July 23, 2026 • 09:15 AM", icon: Info, color: "var(--color-secondary)" }
          ].map((n) => {
            const Icon = n.icon;
            return (
              <div 
                key={n.id}
                style={{ display: "flex", gap: "16px", padding: "16px", borderRadius: "12px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)", alignItems: "flex-start" }}
              >
                <div style={{ width: "36px", height: "36px", borderRadius: "50%", backgroundColor: "rgba(255,255,255,0.03)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: "2px" }}>
                  <Icon size={18} color={n.color} />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: "600", color: "#FFFFFF" }}>{n.msg}</span>
                  <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{n.date}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Notifications;

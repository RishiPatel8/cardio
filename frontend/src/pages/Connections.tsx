import React from "react";
import { Heart, Activity, Plus } from "lucide-react";

const Connections: React.FC = () => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Wearable Device & SDK Connections</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Integrate external biosensing hardware and software layers to automate heart rate logging.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
        {/* Google Fit Panel */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px", position: "relative", overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Activity color="var(--color-primary)" size={24} />
            <div>
              <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Google Fit Integration</h3>
              <span style={{ fontSize: "0.65rem", color: "var(--color-normal)" }}>• Connected</span>
            </div>
          </div>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", minHeight: "60px" }}>
            Synchronizes daily activity, calories, step metrics, and average pulse data directly from the cloud.
          </p>
          <button className="btn-secondary" style={{ width: "100%", justifyContent: "center" }}>
            Manage Connection
          </button>
        </div>

        {/* Health Connect Panel */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Heart color="var(--color-secondary)" size={24} />
            <div>
              <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Health Connect (Android)</h3>
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>• Not Configured</span>
            </div>
          </div>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", minHeight: "60px" }}>
            On-device local aggregation database linking Wear OS sensors directly to the CardioGuard Android client.
          </p>
          <button className="btn-primary" style={{ width: "100%", justifyContent: "center" }}>
            <Plus size={14} /> Configure SDK
          </button>
        </div>
      </div>
    </div>
  );
};

export default Connections;

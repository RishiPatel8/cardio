import React from "react";
import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";

const NotFound: React.FC = () => {
  return (
    <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", minHeight: "60vh", padding: "24px" }}>
      <div className="glass-panel" style={{ maxWidth: "450px", textAlign: "center", padding: "40px" }}>
        <div style={{ width: "64px", height: "64px", borderRadius: "50%", backgroundColor: "rgba(255, 45, 85, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
          <ShieldAlert size={32} color="var(--color-primary)" />
        </div>
        <h2 style={{ fontSize: "1.8rem", fontWeight: "800", marginBottom: "8px" }}>404 - Page Not Found</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "24px" }}>
          The requested resource is missing, expired, or unavailable. Verify your URL parameters or navigate home.
        </p>
        <Link to="/dashboard" className="btn-primary" style={{ display: "inline-flex", margin: "0 auto" }}>
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
};

export default NotFound;

import React from "react";
import { FileText, Download, Calendar } from "lucide-react";

const Reports: React.FC = () => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Clinical Diagnostic Reports</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Access, download, and review generated ECG waveform analysis reports compiled for medical reference.
        </p>
      </div>

      <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Recent Diagnostic PDF Exports</h3>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {[
            { id: "1", title: "Cardio Diagnostic PDF Report", date: "July 22, 2026", size: "142 KB", status: "Ready" },
            { id: "2", title: "Weekly Telemetry Rhythm Summary", date: "July 15, 2026", size: "210 KB", status: "Archived" },
            { id: "3", title: "Atrial Fibrillation Risk Review", date: "July 08, 2026", size: "185 KB", status: "Archived" }
          ].map((r) => (
            <div 
              key={r.id}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", borderRadius: "12px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <FileText size={20} color="var(--color-primary)" />
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: "600" }}>{r.title}</span>
                  <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "4px" }}>
                    <Calendar size={10} /> {r.date} • {r.size}
                  </span>
                </div>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button 
                  onClick={() => alert(`Downloading ${r.title}...`)} 
                  className="btn-secondary" 
                  style={{ padding: "8px 12px", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}
                >
                  <Download size={12} /> Save
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Reports;

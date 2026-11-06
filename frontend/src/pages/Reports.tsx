import React, { useState, useEffect } from "react";
import { FileText, Download, Calendar, Loader2 } from "lucide-react";
import { getUserToken } from "../services/auth";

interface ReportItem {
  id: string;
  title: string;
  created_at: string;
  report_url: string;
}

const Reports: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const token = await getUserToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${apiUrl}/reports?limit=20`, { headers });
      if (res.ok) {
        const data = await res.json();
        setReports(data || []);
      }
    } catch (e) {
      console.error("Failed to fetch reports:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDownload = async (reportUrl: string, title: string, id: string) => {
    setDownloadingId(id);
    try {
      const token = await getUserToken();
      const downloadHeaders: Record<string, string> = {};
      if (token) downloadHeaders["Authorization"] = `Bearer ${token}`;

      const res = await fetch(reportUrl, { headers: downloadHeaders });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const filename = `${title.replace(/[^a-zA-Z0-9_-]/g, "_")}.pdf`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        window.open(reportUrl, "_blank");
      }
    } catch (e) {
      console.error("Download failed:", e);
      window.open(reportUrl, "_blank");
    } finally {
      setDownloadingId(null);
    }
  };

  const handleGenerateSample = async () => {
    setDownloadingId("sample");
    try {
      const token = await getUserToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${apiUrl}/reports/generate`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          title: `Cardio Diagnostic PDF Report - ${new Date().toLocaleDateString()}`,
          prediction_class: "Conduction Block",
          confidence: 53.08,
          model_version: "v6-canonical (1D CNN)",
          probability_vector: [0.009, 0.032, 0.531, 0.428],
          inference_time_ms: 218,
          patient_age: 69.0,
          patient_sex: 0,
          signal_quality: "GOOD",
          avg_bpm: 74.0,
          rmssd_ms: 35.0,
          sdrr_ms: 45.0,
          explainable_insights: [
            "Consistent with Conduction Block (53.1% confidence)",
            "MIT-BIH Record 100 Lead MLII telemetry evaluated",
            "180 consecutive 10-second segments analyzed"
          ],
          explanation_values: [
            { feature: "time_125", contribution: 0.184 },
            { feature: "time_280", contribution: 0.152 },
            { feature: "time_600", contribution: 0.118 },
            { feature: "time_750", contribution: 0.096 },
            { feature: "time_30", contribution: 0.062 }
          ],
          dataset_metadata: {
            fileName: "MIT-BIH Record 100",
            recordsCount: 180,
            fs: "100 Hz"
          }
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.report_url) {
          await handleDownload(data.report_url, data.title || "Cardio_Diagnostic_Report", data.id);
          fetchReports();
        }
      }
    } catch (e) {
      console.error("Failed to generate sample report:", e);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Clinical Diagnostic Reports</h2>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Access, download, and review generated ECG waveform analysis reports compiled for medical reference.
        </p>
      </div>

      <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Recent Diagnostic PDF Exports</h3>
          <button 
            onClick={handleGenerateSample}
            disabled={downloadingId !== null}
            className="btn-primary"
            style={{ padding: "8px 14px", fontSize: "0.8rem" }}
          >
            {downloadingId === "sample" ? <Loader2 size={14} className="spin-animation" /> : <FileText size={14} />}
            Generate New Report
          </button>
        </div>
        
        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "30px", color: "var(--text-secondary)" }}>
            <Loader2 size={24} className="spin-animation" />
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {reports.length > 0 ? (
              reports.map((r) => (
                <div 
                  key={r.id}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", borderRadius: "12px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)" }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <FileText size={20} color="var(--color-primary)" />
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: "600" }}>{r.title}</span>
                      <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "4px" }}>
                        <Calendar size={10} /> {new Date(r.created_at).toLocaleDateString()} • PDF Document
                      </span>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button 
                      onClick={() => handleDownload(r.report_url, r.title, r.id)}
                      disabled={downloadingId === r.id}
                      className="btn-secondary" 
                      style={{ padding: "8px 12px", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}
                    >
                      {downloadingId === r.id ? <Loader2 size={12} className="spin-animation" /> : <Download size={12} />}
                      Save
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: "24px", textAlign: "center", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                No diagnostic PDF reports generated yet. Click "Generate New Report" or run AI Detection on the Dashboard.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Reports;

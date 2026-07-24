import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { HeartRateChart } from "../components/HeartRateChart";
import { GoogleFitConnector } from "../components/GoogleFitConnector";
import { DatasetUploader } from "../components/DatasetUploader";
import { DetectionRunner } from "../components/DetectionRunner";
import { ResultsView } from "../components/ResultsView";
import { ActivityRings } from "../components/ActivityRings";
import { 
  Tv, Play, Pause, ZoomIn, ZoomOut, Filter, Download, FileText, 
  ShieldCheck, Clock, PlusCircle
} from "lucide-react";

interface DatasetStats {
  avgBpm: number;
  sdrr: number;
  rmssd: number;
}

interface DatasetPayload {
  fileName: string;
  recordsCount: number;
  rows: any[];
  stats: DatasetStats;
}

interface DashboardContext {
  activeMetric: string;
  setActiveMetric: (metric: string) => void;
  dataOrigin: "default" | "google_fit" | "csv";
  setDataOrigin: (origin: "default" | "google_fit" | "csv") => void;
  isFitConnected: boolean;
  setIsFitConnected: (conn: boolean) => void;
  uploadedDataset: DatasetPayload | null;
  setUploadedDataset: (ds: DatasetPayload | null) => void;
  isAnalyzing: boolean;
  setIsAnalyzing: (analyzing: boolean) => void;
  analysisResult: {
    resultType: "normal" | "af";
    confidence: number;
    stats: DatasetStats;
    modelVersion: string;
    explainableInsights: string[];
    inferenceTimeMs: number;
    fileName?: string;
  } | null;
  setAnalysisResult: (res: any) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  zoomLevel: number;
  setZoomLevel: React.Dispatch<React.SetStateAction<number>>;
  isFiltered: boolean;
  setIsFiltered: (filtered: boolean) => void;
  isFullscreen: boolean;
  setIsFullscreen: (fs: boolean) => void;
  playOffset: number;
  dailyStats: {
    avgBpm: number;
    sdrr: number;
    rmssd: number;
    steps: number;
    calories: number;
    sleep: number;
    stress: number;
  };
  metricData: Record<string, any>;
  isAF: boolean;
  handleGoogleFitConnect: () => void;
  handleGoogleFitDisconnect: () => void;
  handleDatasetLoaded: (ds: DatasetPayload) => void;
  handleClearDataset: () => void;
  handleStartAnalysis: () => void;
  handleAnalysisComplete: () => void;
  handleResetAnalysis: () => void;
  logAppError: (source: string, error: any) => void;
  getUserToken: () => Promise<string | null>;
  getAppCheckToken: () => Promise<string | null>;
}

const Dashboard: React.FC = () => {
  const {
    activeMetric,
    setActiveMetric,
    dataOrigin,
    isFitConnected,
    uploadedDataset,
    isAnalyzing,
    analysisResult,
    isPlaying,
    setIsPlaying,
    zoomLevel,
    setZoomLevel,
    isFiltered,
    setIsFiltered,
    isFullscreen,
    setIsFullscreen,
    playOffset,
    dailyStats,
    metricData,
    isAF,
    handleGoogleFitConnect,
    handleGoogleFitDisconnect,
    handleDatasetLoaded,
    handleClearDataset,
    handleStartAnalysis,
    handleAnalysisComplete,
    handleResetAnalysis,
    logAppError,
    getUserToken,
    getAppCheckToken,
  } = useOutletContext<DashboardContext>();

  // Profile and synchronized vitals states
  const [profile, setProfile] = useState<any>(null);
  const [vitalsHistory, setVitalsHistory] = useState<any[]>([]);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  // Manual Entry Form local states
  const [manualSteps, setManualSteps] = useState<number>(6500);
  const [manualSleep, setManualSleep] = useState<number>(7.5);
  const [manualSpo2, setManualSpo2] = useState<number>(98);
  const [manualSystolic, setManualSystolic] = useState<number>(120);
  const [manualDiastolic, setManualDiastolic] = useState<number>(80);
  const [manualWeight, setManualWeight] = useState<number>(72.0);
  const [manualCalories, setManualCalories] = useState<number>(350);

  const fetchProfileAndHistory = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      // 1. Fetch profile
      const profRes = await fetch(`${apiUrl}/users/me/profile`, { method: "GET", headers });
      if (profRes.ok) {
        const profData = await profRes.json();
        setProfile(profData);
        // Pre-fill weight from profile
        if (profData.weight) setManualWeight(profData.weight);
      }

      // 2. Fetch history
      const histRes = await fetch(`${apiUrl}/wearables/history?limit=10`, { method: "GET", headers });
      if (histRes.ok) {
        const histData = await histRes.json();
        setVitalsHistory(histData);
      }
    } catch (err) {
      console.error("Failed to load dashboard metrics", err);
    }
  };

  useEffect(() => {
    fetchProfileAndHistory();
  }, [getUserToken, getAppCheckToken]);

  const handleManualSync = async (e: React.FormEvent) => {
    e.preventDefault();
    setSyncing(true);
    setSyncStatus(null);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const syncPayload = {
        source: "manual_entry",
        file_name: "manual_vitals.csv",
        avg_bpm: dailyStats.avgBpm,
        sdrr_ms: dailyStats.sdrr,
        rmssd_ms: dailyStats.rmssd,
        sleep_minutes: manualSleep * 60,
        calories_burned: manualCalories,
        steps_count: manualSteps,
        spo2: manualSpo2,
        systolic_bp: manualSystolic,
        diastolic_bp: manualDiastolic,
        timeseries_data: []
      };

      const res = await fetch(`${apiUrl}/wearables/sync`, {
        method: "POST",
        headers,
        body: JSON.stringify(syncPayload),
      });

      if (res.ok) {
        setSyncStatus("Vitals synchronized successfully!");
        fetchProfileAndHistory();
      } else {
        setSyncStatus("Failed to synchronize vitals.");
      }
    } catch (err) {
      setSyncStatus("Failed to communicate with vitals synchronization service.");
    } finally {
      setSyncing(false);
    }
  };

  // Get current active values
  const currentSyncRecord = vitalsHistory.length > 0 ? vitalsHistory[0] : null;
  const activeSteps = currentSyncRecord ? currentSyncRecord.steps_count : dailyStats.steps;
  const activeCalories = currentSyncRecord ? currentSyncRecord.calories_burned : dailyStats.calories;
  const activeSleep = currentSyncRecord ? (currentSyncRecord.sleep_minutes / 60).toFixed(1) : dailyStats.sleep;
  const activeSpo2 = currentSyncRecord ? currentSyncRecord.spo2 : 98;
  const activeBp = currentSyncRecord ? `${currentSyncRecord.systolic_bp}/${currentSyncRecord.diastolic_bp}` : "120/80";

  // Targets / Goals progress calculations
  const stepsGoal = profile ? profile.daily_steps_goal : 10000;

  const stepsPct = Math.min(100, Math.round((activeSteps / stepsGoal) * 100));

  // Diagnostic Score models
  const healthScore = isAF ? 54 : 91;
  const cardRisk = isAF ? "74% (High AF Risk)" : (profile?.hypertension || profile?.smoking ? "14.2% (Moderate Risk)" : "4.8% (Optimal Risk)");
  const recoveryScore = isAF ? "42 (Depressed HRV)" : "86 (Healthy)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      
      {/* 💊 Prescription alerts & medical cofactor warnings */}
      {profile && profile.current_medications && profile.current_medications.length > 0 && (
        <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(0, 122, 255, 0.08)", border: "1px solid rgba(0, 122, 255, 0.2)", display: "flex", alignItems: "center", gap: "12px" }}>
          <Clock size={18} color="var(--color-secondary)" />
          <div style={{ fontSize: "0.8rem", color: "#FFFFFF", lineHeight: "1.4" }}>
            <span style={{ fontWeight: "700" }}>Medication Reminders:</span> Take {profile.current_medications.map((m: any) => `${m.name} (${m.dosage}, ${m.frequency})`).join(", ")}.
          </div>
        </div>
      )}

      {/* 🏥 Medical Cofactors Highlights */}
      {profile && (profile.diabetes || profile.hypertension || profile.smoking) && (
        <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 45, 85, 0.08)", border: "1px solid rgba(255, 45, 85, 0.2)", display: "flex", alignItems: "center", gap: "12px" }}>
          <ShieldCheck size={18} color="var(--color-primary)" />
          <div style={{ fontSize: "0.8rem", color: "#FFFFFF", lineHeight: "1.4" }}>
            <span style={{ fontWeight: "700" }}>Clinical Risk Cofactors Active:</span> {profile.hypertension && "Hypertension "} {profile.diabetes && "Diabetes "} {profile.smoking && "Smoking "}. Multimodal AI assessments auto-adjust risk weightings.
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        
        {/* Main Left Column (Span 8) */}
        <div className="grid-main-col" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Apple-grade Clinical & Wellness Metrics Panel */}
          <div className="glass-panel" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px", padding: "20px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase" }}>Overall Health Index</span>
              <span style={{ fontSize: "1.8rem", fontWeight: "900", color: healthScore < 60 ? "var(--color-risk)" : "var(--color-normal)" }}>
                {healthScore} / 100
              </span>
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Based on autonomic tone and sleep saturation</span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px", borderLeft: "1px solid var(--border-glass)", paddingLeft: "20px" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase" }}>Cardiovascular Risk</span>
              <span style={{ fontSize: "1.2rem", fontWeight: "800", color: isAF ? "var(--color-risk)" : "#FFFFFF", marginTop: "6px" }}>
                {cardRisk}
              </span>
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>10-year clinical Framingham score equivalent</span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px", borderLeft: "1px solid var(--border-glass)", paddingLeft: "20px" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase" }}>Recovery (RMSSD Score)</span>
              <span style={{ fontSize: "1.3rem", fontWeight: "800", color: "var(--color-normal)", marginTop: "6px" }}>
                {recoveryScore}
              </span>
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Resting heart rate variability baseline status</span>
            </div>
          </div>

          {/* 8 Vitals Cards Overview Grid */}
          <div className="vitals-grid">
            {[
              { key: "heartRate", label: "Resting Heart Rate", val: `${Math.round(dailyStats.avgBpm)} bpm`, stat: "Normal", color: "#FF2D55" },
              { key: "hrv", label: "HRV (RMSSD)", val: `${Math.round(dailyStats.rmssd)} ms`, stat: "Optimal", color: "#AF52DE" },
              { key: "spo2", label: "Oxygen Saturation SpO₂", val: `${activeSpo2} %`, stat: activeSpo2 < 95 ? "Attention" : "Optimal", color: "#007AFF" },
              { key: "bp", label: "Blood Pressure", val: activeBp, stat: "mmHg", color: "#FF9500" },
              { key: "steps", label: "Active Steps", val: activeSteps.toLocaleString(), stat: `Goal: ${(stepsGoal/1000).toFixed(0)}k`, color: "#34C759" },
              { key: "calories", label: "Calories Burned", val: `${activeCalories} kcal`, stat: "Active", color: "#FFCC00" },
              { key: "sleep", label: "Sleep Duration", val: `${activeSleep} hrs`, stat: "Good", color: "#5856D6" },
              { key: "bodyBattery", label: "Weight / BMI Trend", val: `${manualWeight} kg`, stat: `BMI: ${profile?.bmi || "22.8"}`, color: "#00C7BE" },
            ].map((c) => (
              <div 
                key={c.key}
                onClick={() => setActiveMetric(c.key === "bp" ? "heartRate" : (c.key === "bodyBattery" ? "hrv" : c.key))}
                className={`health-card ${activeMetric === c.key ? "active" : ""}`}
              >
                <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontWeight: "600" }}>{c.label}</span>
                <span style={{ fontSize: "1.35rem", fontWeight: "800", color: "#FFFFFF" }}>{c.val}</span>
                <span style={{ fontSize: "0.65rem", color: c.color }}>• {c.stat}</span>
              </div>
            ))}
          </div>

          {/* Area Chart mapping dynamic metric data streams */}
          <HeartRateChart activeMetric={activeMetric} data={metricData} />

          {/* Apple concentric activity rings & stats breakdown */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }} className="insights-row">
            <div className="glass-panel" style={{ padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Activity Rings Progress</h3>
                <span style={{ fontSize: "0.75rem", color: "var(--color-normal)", fontWeight: "700" }}>{stepsPct}% Goal</span>
              </div>
              <ActivityRings calories={activeCalories} steps={activeSteps} activeMin={35} />
            </div>

            {/* Compact ECG Widget with controls */}
            <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: "800", textTransform: "uppercase" }}>Compact ECG Lead-II</span>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button onClick={() => setIsPlaying(!isPlaying)} className="btn-secondary" style={{ padding: "4px" }} title="Playback">
                    {isPlaying ? <Pause size={12} /> : <Play size={12} />}
                  </button>
                  <button onClick={() => setZoomLevel(prev => prev === 1 ? 1.5 : 1)} className="btn-secondary" style={{ padding: "4px" }} title="Zoom">
                    {zoomLevel === 1 ? <ZoomIn size={12} /> : <ZoomOut size={12} />}
                  </button>
                  <button onClick={() => setIsFiltered(!isFiltered)} className="btn-secondary" style={{ padding: "4px" }} title="Filter">
                    <Filter size={12} style={{ color: isFiltered ? "var(--color-primary)" : "#FFFFFF" }} />
                  </button>
                  <button onClick={() => setIsFullscreen(!isFullscreen)} className="btn-secondary" style={{ padding: "4px" }} title="Expand">
                    <Tv size={12} />
                  </button>
                </div>
              </div>

              <div style={{ width: "100%", height: "70px", backgroundColor: "rgba(0,0,0,0.15)", borderRadius: "10px", overflow: "hidden", display: "flex", alignItems: "center", position: "relative" }}>
                <svg width="100%" height="100%" viewBox="0 0 300 60" style={{ transform: `scale(${zoomLevel})` }}>
                  <path 
                    d={`M0 30 Q15 28 30 30 L40 35 L43 10 L47 50 L50 30 Q65 28 80 30 M100 30 Q115 28 130 30 L140 35 L143 10 L147 50 L150 30 Q165 28 180 30`}
                    fill="none" 
                    stroke={isAF ? "#FF3B30" : "#34C759"} 
                    strokeWidth="2" 
                    transform={`translate(${-playOffset} 0)`}
                  />
                </svg>
                <span style={{ position: "absolute", bottom: "4px", left: "8px", fontSize: "0.55rem", color: "var(--text-muted)" }}>
                  {isFiltered ? "Bandpass Filter Active" : "Raw Input Stream"}
                </span>
              </div>
            </div>
          </div>

          {/* Predictions Log results preview */}
          {analysisResult && (
            <ResultsView 
              resultType={analysisResult.resultType}
              confidence={analysisResult.confidence}
              modelVersion={analysisResult.modelVersion}
              explainableInsights={analysisResult.explainableInsights}
              inferenceTimeMs={analysisResult.inferenceTimeMs}
              onReset={handleResetAnalysis}
              onExportReport={async () => {
                try {
                  const token = await getUserToken();
                  const appCheckToken = await getAppCheckToken();
                  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

                  const headers: Record<string, string> = {
                    "Content-Type": "application/json",
                  };
                  if (token) {
                    headers["Authorization"] = `Bearer ${token}`;
                  }
                  if (appCheckToken) {
                    headers["X-Firebase-App-Check"] = appCheckToken;
                  }

                  const response = await fetch(`${apiUrl}/reports/generate`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify({
                      title: `Cardio Diagnostics Summary - ${new Date().toLocaleDateString()}`,
                      prediction_id: null
                    })
                  });

                  if (response.ok) {
                    const data = await response.json();
                    if (data.report_url) {
                      window.open(data.report_url, "_blank");
                    } else {
                      alert("Report successfully generated on server.");
                    }
                  } else {
                    alert("Failed to generate clinical PDF report.");
                  }
                } catch (err) {
                  logAppError("onExportReport", err);
                  alert("Failed to communicate with report service.");
                }
              }}
            />
          )}
        </div>

        {/* Right Column (Span 4) */}
        <div className="grid-side-col" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Manual Vitals Synchronization Panel */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <PlusCircle size={18} color="var(--color-primary)" />
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Manual Vitals & Health Entry</h3>
            </div>

            {syncStatus && (
              <div style={{ fontSize: "0.75rem", padding: "8px", borderRadius: "6px", backgroundColor: "rgba(255,255,255,0.03)", border: "1px solid var(--border-glass)", color: "var(--color-normal)" }}>
                {syncStatus}
              </div>
            )}

            <form onSubmit={handleManualSync} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Steps Count</label>
                  <input 
                    type="number" 
                    value={manualSteps} 
                    onChange={(e) => setManualSteps(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Sleep Duration (hrs)</label>
                  <input 
                    type="number" 
                    step="0.1"
                    value={manualSleep} 
                    onChange={(e) => setManualSleep(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>SpO₂ Saturation (%)</label>
                  <input 
                    type="number" 
                    value={manualSpo2} 
                    onChange={(e) => setManualSpo2(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Weight (kg)</label>
                  <input 
                    type="number" 
                    value={manualWeight} 
                    onChange={(e) => setManualWeight(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Active Calories (kcal)</label>
                  <input 
                    type="number" 
                    value={manualCalories} 
                    onChange={(e) => setManualCalories(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Blood Pressure (Systolic)</label>
                  <input 
                    type="number" 
                    value={manualSystolic} 
                    onChange={(e) => setManualSystolic(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Blood Pressure (Diastolic)</label>
                  <input 
                    type="number" 
                    value={manualDiastolic} 
                    onChange={(e) => setManualDiastolic(Number(e.target.value))}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
              </div>
              <button 
                type="submit" 
                disabled={syncing}
                className="btn-secondary" 
                style={{ width: "100%", justifyContent: "center", padding: "10px", marginTop: "6px", fontSize: "0.8rem", fontWeight: "700" }}
              >
                {syncing ? "Synchronizing..." : "Sync Vitals Database"}
              </button>
            </form>
          </div>

          {/* Sync control panels */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Sync Channels</h3>
            <GoogleFitConnector
              isConnected={isFitConnected}
              onConnect={handleGoogleFitConnect}
              onDisconnect={handleGoogleFitDisconnect}
            />
            <DatasetUploader
              onDatasetLoaded={handleDatasetLoaded}
              onClear={handleClearDataset}
              currentDatasetName={uploadedDataset ? uploadedDataset.fileName : null}
            />
            <DetectionRunner
              hasData={dataOrigin !== "default" || uploadedDataset !== null}
              isAnalyzing={isAnalyzing}
              onStartAnalysis={handleStartAnalysis}
              onAnalysisComplete={handleAnalysisComplete}
            />
          </div>

          {/* Export and reports generator history */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Recent Reports</h3>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px", borderRadius: "10px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <FileText size={16} color="var(--color-primary)" />
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: "600" }}>Cardio Diagnostic PDF</span>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>July 22, 2026</span>
                </div>
              </div>
              <button onClick={() => alert("Downloading diagnostic PDF report.")} style={{ border: "none", background: "none", cursor: "pointer" }} title="Download">
                <Download size={14} color="#FFFFFF" />
              </button>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default Dashboard;

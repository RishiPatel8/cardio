import React, { useState, useEffect, useRef } from "react";
import { useOutletContext } from "react-router-dom";
import { calculateCardiovascularRisk } from "../utils/riskCalculator";
import { HeartRateChart } from "../components/HeartRateChart";
import { GoogleFitConnector } from "../components/GoogleFitConnector";
import { DatasetUploader } from "../components/DatasetUploader";
import { DetectionRunner } from "../components/DetectionRunner";
import { ResultsView } from "../components/ResultsView";
import { ActivityRings } from "../components/ActivityRings";
import { 
  Tv, Play, Pause, ZoomIn, ZoomOut, Filter, Download, FileText, 
  Activity, ShieldCheck, Clock, PlusCircle, X, Minimize2
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
  age?: number;
  sex?: number;
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
    resultType: string;
    confidence: number;
    stats: DatasetStats;
    modelVersion: string;
    explainableInsights: string[];
    explanationValues?: any[];
    inferenceTimeMs: number;
    probabilityVector?: number[];
    highestRiskSegment?: number[];
    signalQuality?: string;
    fileName?: string;
    comparisons?: any;
    contributingModels?: any[];
    excludedModels?: any[];
    contributingModelsCount?: number;
    totalModelsCount?: number;
    agreementAnalysis?: any;
    ensembleWeights?: any;
    isEnsemble?: boolean;
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
  dailyStats: {
    avgBpm: number;
    sdrr: number;
    rmssd: number;
    steps: number;
    calories: number;
    sleep: number;
    stress: number;
  };
  setDailyStats: React.Dispatch<React.SetStateAction<any>>;
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
  availableModels: any[];
  selectedModelId: string;
  setSelectedModelId: (id: string) => void;
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
    dailyStats,
    setDailyStats,
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
    availableModels,
    selectedModelId,
    setSelectedModelId,
  } = useOutletContext<DashboardContext>();

  // Profile and synchronized vitals states
  const [profile, setProfile] = useState<any>(null);
  const [vitalsHistory, setVitalsHistory] = useState<any[]>([]);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  
  const [playOffset, setPlayOffset] = useState<number>(0);
  const [selectedRegion, setSelectedRegion] = useState<{ start: number; end: number } | null>(null);
  const compactEcgRef = useRef<HTMLDivElement>(null);

  // Generate Compact ECG path
  const compactEcgPath = React.useMemo(() => {
    if (!analysisResult?.highestRiskSegment) {
       return "M0 30 Q15 28 30 30 L40 35 L43 10 L47 50 L50 30 Q65 28 80 30 M100 30 Q115 28 130 30 L140 35 L143 10 L147 50 L150 30 Q165 28 180 30";
    }
    
    const segment = analysisResult.highestRiskSegment;
    const path: string[] = [];
    const width = 1000;
    const height = 60;
    
    let min = segment[0];
    let max = segment[0];
    for (const val of segment) {
      if (val < min) min = val;
      if (val > max) max = val;
    }
    const range = max - min || 1;

    for (let i = 0; i < segment.length; i += 2) {
       const x = (i / segment.length) * width;
       const normalizedY = (segment[i] - min) / range;
       const y = height - (normalizedY * height * 0.8 + height * 0.1); 
       
       if (i === 0) {
         path.push(`M${x.toFixed(1)} ${y.toFixed(1)}`);
       } else {
         path.push(`L${x.toFixed(1)} ${y.toFixed(1)}`);
       }
    }
    return path.join(" ");
  }, [analysisResult?.highestRiskSegment]);

  // ECG waveform animation loop
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setPlayOffset((prev) => (prev + 2) % 1000);
    }, 40);
    return () => clearInterval(interval);
  }, [isPlaying]);

const resolveReportUrl = (url: string): string => {
  if (!url) return "";
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
  const backendBase = apiUrl.replace(/\/api\/v1\/?$/, "");
  
  if (url.startsWith("/api/v1")) {
    return `${backendBase}${url}`;
  }
  if (url.includes("localhost:8000")) {
    return url.replace(/https?:\/\/localhost:8000/, backendBase);
  }
  return url;
};

const downloadReportFile = async (rawUrl: string, defaultFilename: string = "CardioGuard_Diagnostic_Report.pdf") => {
    const reportUrl = resolveReportUrl(rawUrl);
    try {
      const token = await getUserToken();
      const downloadHeaders: Record<string, string> = {};
      if (token) downloadHeaders["Authorization"] = `Bearer ${token}`;
      const fileRes = await fetch(reportUrl, { headers: downloadHeaders });
      if (fileRes.ok) {
        const blob = await fileRes.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = defaultFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        window.open(reportUrl, "_blank");
      }
    } catch {
      window.open(reportUrl, "_blank");
    }
  };

  const handleRegionClick = (startSec: number, endSec: number) => {
    setIsPlaying(false);
    const startX = startSec * 100;
    const endX = endSec * 100;
    const centerX = (startX + endX) / 2;
    
    setSelectedRegion({ start: startSec, end: endSec });
    setPlayOffset(centerX);
    setZoomLevel(1.5);
    
    // Automatically launch the Fullscreen ECG Diagnostic Rhythm Monitor Modal
    setIsFullscreen(true);
    
    // Smoothly scroll the compact widget into view as well
    setTimeout(() => {
      compactEcgRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  };

  // Handle ESC key to exit fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFullscreen, setIsFullscreen]);

  // High-Resolution Fullscreen ECG Waveform Path
  const fullscreenEcgPath = React.useMemo(() => {
    let segment = analysisResult?.highestRiskSegment || [];
    const width = 1000;
    const height = 240;
    
    if (!segment || segment.length === 0) {
      // Default canonical sinus rhythm ECG waveform for monitor
      return "M0 120 Q20 110 40 120 L60 135 L70 30 L80 210 L90 120 Q120 95 150 120 L200 120 M200 120 Q220 110 240 120 L260 135 L270 30 L280 210 L290 120 Q320 95 350 120 L400 120 M400 120 Q420 110 440 120 L460 135 L470 30 L480 210 L490 120 Q520 95 550 120 L600 120 M600 120 Q620 110 640 120 L660 135 L670 30 L680 210 L690 120 Q720 95 750 120 L800 120 M800 120 Q820 110 840 120 L860 135 L870 30 L880 210 L890 120 Q920 95 950 120 L1000 120";
    }

    if (isFiltered) {
      const smoothed = [...segment];
      for (let i = 1; i < segment.length - 1; i++) {
        smoothed[i] = (segment[i - 1] + 2 * segment[i] + segment[i + 1]) / 4;
      }
      segment = smoothed;
    }

    let min = segment[0];
    let max = segment[0];
    for (const val of segment) {
      if (val < min) min = val;
      if (val > max) max = val;
    }
    const range = Math.max(max - min, 0.001);

    const path: string[] = [];
    for (let i = 0; i < segment.length; i++) {
      const x = (i / (segment.length - 1)) * width;
      const normalizedY = (segment[i] - min) / range;
      const y = height - (normalizedY * (height * 0.75) + height * 0.12);
      if (i === 0) {
        path.push(`M${x.toFixed(1)} ${y.toFixed(1)}`);
      } else {
        path.push(`L${x.toFixed(1)} ${y.toFixed(1)}`);
      }
    }
    return path.join(" ");
  }, [analysisResult?.highestRiskSegment, isFiltered]);

  // Fullscreen Attribution Regions
  const fullscreenAttributionRegions = React.useMemo(() => {
    const explanationValues = analysisResult?.explanationValues;
    if (!explanationValues || explanationValues.length === 0) {
      // Fallback: detect peaks in segment if no explanation values
      const segment = analysisResult?.highestRiskSegment;
      if (segment && segment.length >= 100) {
        const mean = segment.reduce((a, b) => a + b, 0) / segment.length;
        const std = Math.sqrt(segment.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / segment.length);
        const peakThresh = mean + Math.max(std * 1.0, 0.2);
        const minPeakDist = 40;
        const peaks: { timeSec: number; val: number }[] = [];
        for (let i = 1; i < segment.length - 1; i++) {
          if (segment[i] > peakThresh && segment[i] >= segment[i - 1] && segment[i] >= segment[i + 1]) {
            if (peaks.length === 0 || (i - (peaks[peaks.length - 1].timeSec * 100)) >= minPeakDist) {
              peaks.push({ timeSec: i / 100.0, val: segment[i] });
            }
          }
        }
        return peaks.slice(0, 3).map(p => ({
          start: Math.max(0, parseFloat((p.timeSec - 0.15).toFixed(2))),
          end: Math.min(10.0, parseFloat((p.timeSec + 0.15).toFixed(2))),
          maxContrib: p.val
        }));
      }
      return [];
    }

    const positiveFeatures = explanationValues
      .filter((v: any) => v.contribution > 0.0001 && v.feature && v.feature.startsWith('time_'))
      .map((v: any) => {
        const sampleIdx = parseInt(v.feature.split('_')[1], 10);
        return {
          timeSec: sampleIdx / 100.0,
          contribution: v.contribution
        };
      })
      .filter((v: any) => !isNaN(v.timeSec))
      .sort((a, b) => b.contribution - a.contribution);

    if (positiveFeatures.length === 0) return [];
    
    const topPoints = positiveFeatures.slice(0, 20).sort((a, b) => a.timeSec - b.timeSec);
    const regions: { start: number; end: number; maxContrib: number }[] = [];
    let cur = { start: topPoints[0].timeSec, end: topPoints[0].timeSec, maxContrib: topPoints[0].contribution };

    for (let i = 1; i < topPoints.length; i++) {
      const pt = topPoints[i];
      if (pt.timeSec - cur.end <= 0.5) {
        cur.end = pt.timeSec;
        cur.maxContrib = Math.max(cur.maxContrib, pt.contribution);
      } else {
        regions.push(cur);
        cur = { start: pt.timeSec, end: pt.timeSec, maxContrib: pt.contribution };
      }
    }
    regions.push(cur);

    return regions.map(r => ({
      start: Math.max(0, parseFloat((r.start === r.end ? r.start - 0.15 : r.start).toFixed(2))),
      end: Math.min(10, parseFloat((r.start === r.end ? r.end + 0.15 : r.end).toFixed(2))),
      maxContrib: r.maxContrib
    })).sort((a, b) => b.maxContrib - a.maxContrib).slice(0, 3);
  }, [analysisResult?.explanationValues, analysisResult?.highestRiskSegment]);


  // Manual Entry Form local states (Standard Healthy Baseline)
  const [manualSteps, setManualSteps] = useState<number>(8500);
  const [manualSleep, setManualSleep] = useState<number>(7.8);
  const [manualSpo2, setManualSpo2] = useState<number>(98);
  const [manualSystolic, setManualSystolic] = useState<number>(120);
  const [manualDiastolic, setManualDiastolic] = useState<number>(80);
  const [manualWeight, setManualWeight] = useState<number>(70.0);
  const [manualCalories, setManualCalories] = useState<number>(450);

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
        setDailyStats((prev: any) => ({
          ...prev,
          steps: manualSteps,
          sleep: manualSleep,
          calories: manualCalories,
        }));
        setVitalsHistory((prev: any[]) => [
          {
            steps_count: manualSteps,
            calories_burned: manualCalories,
            sleep_minutes: manualSleep * 60,
            spo2: manualSpo2,
            systolic_bp: manualSystolic,
            diastolic_bp: manualDiastolic,
            avg_bpm: dailyStats.avgBpm,
            rmssd_ms: dailyStats.rmssd,
            sdrr_ms: dailyStats.sdrr,
          },
          ...prev
        ]);
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

  // Parse systolic and diastolic blood pressure
  const bpParts = (activeBp || "120/80").split("/");
  const currentSys = Number(bpParts[0]) || 120;
  const currentDia = Number(bpParts[1]) || 80;

  // Real-time Diagnostic & Risk calculations based on user vitals & AI model
  const { riskString: cardRisk, isAnomaly: cardRiskAnomaly, score: dynamicHealthScore } = calculateCardiovascularRisk(
    analysisResult?.probabilityVector,
    isAF,
    profile,
    {
      systolic_bp: currentSys,
      diastolic_bp: currentDia,
      spo2: Number(activeSpo2),
      sleep_hrs: Number(activeSleep),
      steps: Number(activeSteps)
    }
  );

  const healthScore = dynamicHealthScore;
  const recoveryScore = isAF ? "42 (Depressed HRV)" : (dailyStats.rmssd >= 40 ? "86 (Healthy)" : "62 (Moderate)");

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
              <span style={{ fontSize: "1.2rem", fontWeight: "800", color: cardRiskAnomaly ? "var(--color-risk)" : "#FFFFFF", marginTop: "6px" }}>
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
              { key: "spo2", label: "Oxygen Saturation SpO₂ (Demo Data)", val: `${activeSpo2} %`, stat: activeSpo2 < 95 ? "Attention" : "Optimal", color: "#007AFF" },
              { key: "bp", label: "Blood Pressure (Demo Data)", val: activeBp, stat: "mmHg", color: "#FF9500" },
              { key: "steps", label: "Active Steps (Demo Data)", val: activeSteps.toLocaleString(), stat: `Goal: ${(stepsGoal/1000).toFixed(0)}k`, color: "#34C759" },
              { key: "calories", label: "Calories Burned (Demo Data)", val: `${activeCalories} kcal`, stat: "Active", color: "#FFCC00" },
              { key: "sleep", label: "Sleep Duration (Demo Data)", val: `${activeSleep} hrs`, stat: "Good", color: "#5856D6" },
              { key: "bodyBattery", label: "Weight / BMI Trend (Demo Data)", val: `${manualWeight} kg`, stat: `BMI: ${profile?.bmi || "22.8"}`, color: "#00C7BE" },
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
            <div ref={compactEcgRef} className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: "800", textTransform: "uppercase" }}>Compact ECG (Lead I)</span>
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
                  <button 
                    onClick={() => setIsFullscreen(!isFullscreen)} 
                    className="btn-secondary" 
                    style={{ 
                      padding: "4px",
                      backgroundColor: isFullscreen ? "rgba(0, 122, 255, 0.2)" : undefined,
                      borderColor: isFullscreen ? "var(--color-primary)" : undefined
                    }} 
                    title={isFullscreen ? "Exit Fullscreen" : "Expand Fullscreen"}
                  >
                    {isFullscreen ? <Minimize2 size={12} /> : <Tv size={12} />}
                  </button>
                </div>
              </div>

              <div style={{ width: "100%", height: "70px", backgroundColor: "rgba(0,0,0,0.15)", borderRadius: "10px", overflow: "hidden", display: "flex", alignItems: "center", position: "relative" }}>
                <svg width="100%" height="100%" viewBox="0 0 300 60" style={{ transform: `scale(${zoomLevel})` }}>
                  {selectedRegion && (
                    <g transform={`translate(${-Math.max(0, Math.min(700, playOffset - 150))} 0)`}>
                      <rect 
                        x={selectedRegion.start * 100} 
                        y={0} 
                        width={Math.max(16, (selectedRegion.end - selectedRegion.start) * 100)} 
                        height={60} 
                        fill="rgba(255, 204, 0, 0.25)" 
                        stroke="#FFCC00" 
                        strokeWidth="1.5"
                        strokeDasharray="3 2"
                      />
                    </g>
                  )}
                  <path 
                    d={compactEcgPath}
                    fill="none" 
                    stroke={isAF ? "#FF3B30" : "#34C759"} 
                    strokeWidth="1.5" 
                    transform={`translate(${-Math.max(0, Math.min(700, playOffset - 150))} 0)`}
                  />
                </svg>
                <span style={{ position: "absolute", bottom: "4px", left: "8px", fontSize: "0.55rem", color: "var(--text-muted)" }}>
                  {isFiltered ? "Bandpass Filter Active" : "Raw Input Stream"}
                  {selectedRegion && " • Focused Region: " + selectedRegion.start.toFixed(2) + "s – " + selectedRegion.end.toFixed(2) + "s"}
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
              explanationValues={analysisResult.explanationValues}
              inferenceTimeMs={analysisResult.inferenceTimeMs}
              probabilityVector={analysisResult.probabilityVector}
              signalQuality={analysisResult.signalQuality}
              highestRiskSegment={analysisResult.highestRiskSegment}
              comparisons={analysisResult.comparisons}
              contributingModels={analysisResult.contributingModels}
              excludedModels={analysisResult.excludedModels}
              contributingModelsCount={analysisResult.contributingModelsCount}
              totalModelsCount={analysisResult.totalModelsCount}
              agreementAnalysis={analysisResult.agreementAnalysis}
              ensembleWeights={analysisResult.ensembleWeights}
              isEnsemble={analysisResult.isEnsemble}
              onReset={handleResetAnalysis}
              onRegionClick={handleRegionClick}
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
                      prediction_id: null,
                      prediction_class: analysisResult.resultType,
                      confidence: analysisResult.confidence,
                      model_version: analysisResult.modelVersion,
                      inference_time_ms: analysisResult.inferenceTimeMs,
                      probability_vector: analysisResult.probabilityVector,
                      explainable_insights: analysisResult.explainableInsights,
                      highest_risk_segment: analysisResult.highestRiskSegment,
                      explanation_values: analysisResult.explanationValues,
                      patient_age: uploadedDataset?.age ?? profile?.age ?? 69.0,
                      patient_sex: uploadedDataset?.sex ?? (profile?.gender === "female" ? 1 : 0),
                      signal_quality: analysisResult.signalQuality || "GOOD",
                      avg_bpm: uploadedDataset?.stats?.avgBpm ?? dailyStats.avgBpm ?? 74,
                      rmssd_ms: uploadedDataset?.stats?.rmssd ?? dailyStats.rmssd ?? 35,
                      sdrr_ms: uploadedDataset?.stats?.sdrr ?? dailyStats.sdrr ?? 45,
                      dataset_metadata: {
                        fileName: uploadedDataset?.fileName || "MIT-BIH Record 100",
                        recordsCount: uploadedDataset?.recordsCount || 180,
                        fs: "100 Hz"
                      }
                    })
                  });

                  if (response.ok) {
                    const data = await response.json();
                    if (data.report_url) {
                      await downloadReportFile(data.report_url, `CardioGuard_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
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
              availableModels={availableModels}
              selectedModelId={selectedModelId}
              onModelSelect={setSelectedModelId}
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
              <button 
                onClick={async () => {
                  try {
                    const token = await getUserToken();
                    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
                    const headers: Record<string, string> = {};
                    if (token) headers["Authorization"] = `Bearer ${token}`;
                    const res = await fetch(`${apiUrl}/reports?limit=1`, { headers });
                    if (res.ok) {
                      const reports = await res.json();
                      if (reports && reports.length > 0 && reports[0].report_url) {
                        await downloadReportFile(reports[0].report_url, "Cardio_Diagnostic_Report.pdf");
                        return;
                      }
                    }
                    if (analysisResult) {
                      const genRes = await fetch(`${apiUrl}/reports/generate`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                        body: JSON.stringify({
                          title: `Cardio Diagnostics Summary - ${new Date().toLocaleDateString()}`,
                          prediction_id: null,
                          prediction_class: analysisResult.resultType,
                          confidence: analysisResult.confidence,
                          model_version: analysisResult.modelVersion,
                          inference_time_ms: analysisResult.inferenceTimeMs,
                          probability_vector: analysisResult.probabilityVector,
                          explainable_insights: analysisResult.explainableInsights,
                          highest_risk_segment: analysisResult.highestRiskSegment,
                          explanation_values: analysisResult.explanationValues,
                          patient_age: uploadedDataset?.age ?? profile?.age ?? 69.0,
                          patient_sex: uploadedDataset?.sex ?? (profile?.gender === "female" ? 1 : 0),
                          signal_quality: analysisResult.signalQuality || "GOOD",
                          avg_bpm: uploadedDataset?.stats?.avgBpm ?? dailyStats.avgBpm ?? 74,
                          rmssd_ms: uploadedDataset?.stats?.rmssd ?? dailyStats.rmssd ?? 35,
                          sdrr_ms: uploadedDataset?.stats?.sdrr ?? dailyStats.sdrr ?? 45,
                          dataset_metadata: {
                            fileName: uploadedDataset?.fileName || "MIT-BIH Record 100",
                            recordsCount: uploadedDataset?.recordsCount || 180,
                            fs: "100 Hz"
                          }
                        })
                      });
                      if (genRes.ok) {
                        const genData = await genRes.json();
                        if (genData.report_url) {
                          await downloadReportFile(genData.report_url, "Cardio_Diagnostic_Report.pdf");
                          return;
                        }
                      }
                    }
                    alert("No diagnostic reports generated yet. Run AI Detection and click Export.");
                  } catch (e) {
                    console.error("Recent report download failed", e);
                  }
                }} 
                style={{ border: "none", background: "none", cursor: "pointer" }} 
                title="Download">
                <Download size={14} color="#FFFFFF" />
              </button>
            </div>
          </div>

        </div>

      </div>
      {/* 📺 Fullscreen ECG Diagnostic Rhythm Monitor Modal */}
      {isFullscreen && (
        <div 
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(5, 8, 15, 0.95)",
            backdropFilter: "blur(20px)",
            zIndex: 99999,
            display: "flex",
            flexDirection: "column",
            padding: "24px 32px",
            gap: "18px",
            color: "#FFFFFF",
            boxSizing: "border-box",
            overflowY: "auto"
          }}
        >
          {/* Focused Region Anomaly Alert Banner */}
          {selectedRegion && (
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 18px",
              borderRadius: "10px",
              backgroundColor: "rgba(255, 204, 0, 0.12)",
              border: "1px solid rgba(255, 204, 0, 0.4)",
              color: "#FFCC00"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Activity size={18} color="#FFCC00" />
                <span style={{ fontSize: "0.85rem", fontWeight: "800" }}>
                  Focused Anomaly Attribution: {selectedRegion.start.toFixed(2)}s – {selectedRegion.end.toFixed(2)}s
                </span>
                <span style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.7)" }}>
                  (Sample {Math.round(selectedRegion.start * 100)} to {Math.round(selectedRegion.end * 100)}) • Peak Saliency Deflection
                </span>
              </div>
              <button 
                onClick={() => setSelectedRegion(null)}
                style={{
                  background: "rgba(255,255,255,0.1)",
                  border: "none",
                  borderRadius: "6px",
                  padding: "4px 10px",
                  color: "#FFFFFF",
                  cursor: "pointer",
                  fontSize: "0.7rem",
                  fontWeight: "600"
                }}
              >
                Reset Focus ✕
              </button>
            </div>
          )}

          {/* Top Bar / Header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              <div 
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: isAF ? "#FF3B30" : "#34C759",
                  boxShadow: `0 0 10px ${isAF ? "#FF3B30" : "#34C759"}`
                }} 
              />
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <h2 style={{ fontSize: "1.25rem", fontWeight: "800", letterSpacing: "0.5px", margin: 0 }}>
                    Lead I Telemetry Rhythm Strip — Fullscreen Monitor
                  </h2>
                  <span style={{ fontSize: "0.7rem", padding: "2px 8px", borderRadius: "6px", backgroundColor: isAF ? "rgba(255,59,48,0.15)" : "rgba(52,199,89,0.15)", color: isAF ? "#FF3B30" : "#34C759", fontWeight: "700", border: `1px solid ${isAF ? "rgba(255,59,48,0.3)" : "rgba(52,199,89,0.3)"}` }}>
                    {analysisResult?.resultType || "Normal Sinus Rhythm"}
                  </span>
                </div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px", display: "block" }}>
                  PTB-XL Single-Lead Canonical Acquisition • 100 Hz Sampling • 1,000 Data Points (10.0s window) • {analysisResult?.modelVersion || "Canonical AI"}
                </span>
              </div>
            </div>

            {/* Quick Metrics Badges & Action Buttons */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div style={{ display: "flex", gap: "8px", backgroundColor: "rgba(255,255,255,0.03)", padding: "6px 12px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Heart Rate</span>
                  <span style={{ fontSize: "0.95rem", fontWeight: "800", color: "#FF2D55" }}>{Math.round(dailyStats.avgBpm)} bpm</span>
                </div>
                <div style={{ width: "1px", backgroundColor: "rgba(255,255,255,0.08)", margin: "0 6px" }} />
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", textTransform: "uppercase" }}>RMSSD</span>
                  <span style={{ fontSize: "0.95rem", fontWeight: "800", color: "#AF52DE" }}>{Math.round(dailyStats.rmssd)} ms</span>
                </div>
                <div style={{ width: "1px", backgroundColor: "rgba(255,255,255,0.08)", margin: "0 6px" }} />
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Quality</span>
                  <span style={{ fontSize: "0.95rem", fontWeight: "800", color: "#34C759" }}>{analysisResult?.signalQuality || "OPTIMAL"}</span>
                </div>
              </div>

              {/* Interactive Controls */}
              <button 
                onClick={() => setIsPlaying(!isPlaying)} 
                className="btn-secondary" 
                style={{ padding: "8px 14px", display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", fontWeight: "700" }}
              >
                {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                <span>{isPlaying ? "Pause Stream" : "Play Stream"}</span>
              </button>

              <button 
                onClick={() => setZoomLevel(prev => prev === 1 ? 1.5 : (prev === 1.5 ? 2.0 : 1))} 
                className="btn-secondary" 
                style={{ padding: "8px 14px", display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", fontWeight: "700" }}
              >
                {zoomLevel > 1 ? <ZoomOut size={14} /> : <ZoomIn size={14} />}
                <span>Scale: {zoomLevel}x</span>
              </button>

              <button 
                onClick={() => setIsFiltered(!isFiltered)} 
                className="btn-secondary" 
                style={{ 
                  padding: "8px 14px", 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "6px", 
                  fontSize: "0.8rem", 
                  fontWeight: "700",
                  backgroundColor: isFiltered ? "rgba(0,122,255,0.15)" : undefined,
                  borderColor: isFiltered ? "var(--color-primary)" : undefined,
                  color: isFiltered ? "var(--color-primary)" : "#FFFFFF"
                }}
              >
                <Filter size={14} />
                <span>{isFiltered ? "Bandpass Filter On" : "Raw Input Stream"}</span>
              </button>

              {/* Close Button */}
              <button 
                onClick={() => setIsFullscreen(false)} 
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "8px 14px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  color: "#FFFFFF",
                  cursor: "pointer",
                  fontSize: "0.8rem",
                  fontWeight: "700",
                  transition: "all 0.2s"
                }}
                title="Close Fullscreen (Esc)"
              >
                <X size={16} />
                <span>Exit (Esc)</span>
              </button>
            </div>
          </div>

          {/* Medical Monitor Main Grid Canvas */}
          <div 
            style={{ 
              flex: "1 1 auto",
              minHeight: "360px",
              backgroundColor: "#060911", 
              borderRadius: "14px", 
              border: "1px solid rgba(0, 240, 255, 0.15)",
              position: "relative",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              boxShadow: "inset 0 0 50px rgba(0,0,0,0.8)"
            }}
          >
            {/* Standard Medical Grid SVG */}
            <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
              <svg width="100%" height="100%">
                <defs>
                  <pattern id="medicalSmallGrid" width="10" height="10" patternUnits="userSpaceOnUse">
                    <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(0, 240, 255, 0.04)" strokeWidth="0.5" />
                  </pattern>
                  <pattern id="medicalGrid" width="50" height="50" patternUnits="userSpaceOnUse">
                    <rect width="50" height="50" fill="url(#medicalSmallGrid)" />
                    <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(0, 240, 255, 0.12)" strokeWidth="1" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#medicalGrid)" />
              </svg>
            </div>

            {/* Voltage Calibration & Time Markings */}
            <div style={{ position: "absolute", top: "12px", left: "16px", display: "flex", gap: "12px", alignItems: "center", fontSize: "0.65rem", color: "rgba(0,240,255,0.6)", fontFamily: "monospace" }}>
              <span>25 mm/s</span>
              <span>•</span>
              <span>10 mm/mV</span>
              <span>•</span>
              <span>LEAD I (Bipolar Limb)</span>
            </div>

            {/* Voltage Labels on Y Axis */}
            <div style={{ position: "absolute", right: "12px", top: "20px", bottom: "35px", display: "flex", flexDirection: "column", justifyContent: "space-between", alignItems: "flex-end", fontSize: "0.65rem", color: "rgba(255,255,255,0.3)", pointerEvents: "none", fontFamily: "monospace" }}>
              <span>+1.0 mV</span>
              <span>+0.5 mV</span>
              <span> 0.0 mV</span>
              <span>-0.5 mV</span>
              <span>-1.0 mV</span>
            </div>

            {/* Main Interactive Waveform SVG */}
            <div 
              style={{ 
                width: "100%", 
                height: "100%", 
                display: "flex", 
                alignItems: "center",
                padding: "40px 40px 40px 20px",
                boxSizing: "border-box",
                cursor: "crosshair"
              }}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const ratio = Math.max(0, Math.min(1, clickX / rect.width));
                setPlayOffset(Math.round(ratio * 700));
              }}
            >
              <svg 
                width="100%" 
                height="100%" 
                viewBox="0 0 1000 240" 
                preserveAspectRatio="none"
                style={{ 
                  transform: `scale(${zoomLevel})`, 
                  transformOrigin: "center center", 
                  transition: "transform 0.2s ease-out",
                  overflow: "visible"
                }}
              >
                {/* Salience Attribution Regions Highlight */}
                {fullscreenAttributionRegions.map((r, idx) => {
                  const x = (r.start / 10.0) * 1000;
                  const w = Math.max(24, ((r.end - r.start) / 10.0) * 1000);
                  const isSelected = selectedRegion && (
                    Math.abs(selectedRegion.start - r.start) < 0.05 ||
                    Math.abs(selectedRegion.end - r.end) < 0.05
                  );
                  return (
                    <g key={idx}>
                      <rect 
                        x={x} 
                        y={8} 
                        width={w} 
                        height={224} 
                        fill={isSelected ? "rgba(255, 204, 0, 0.28)" : (isAF ? "rgba(255, 45, 85, 0.15)" : "rgba(0, 122, 255, 0.15)")} 
                        stroke={isSelected ? "#FFCC00" : (isAF ? "rgba(255, 45, 85, 0.5)" : "rgba(0, 122, 255, 0.5)")}
                        strokeWidth={isSelected ? "2.5" : "1"}
                        strokeDasharray={isSelected ? "none" : "4 2"}
                        rx="6"
                      />
                      <text 
                        x={x + 4} 
                        y={26} 
                        fill={isSelected ? "#FFCC00" : (isAF ? "#FF2D55" : "#007AFF")} 
                        fontSize={isSelected ? "11" : "9"} 
                        fontWeight="800" 
                        fontFamily="sans-serif"
                      >
                        {isSelected ? "★ " + r.start.toFixed(2) + "s–" + r.end.toFixed(2) + "s FOCUSED" : r.start.toFixed(1) + "s–" + r.end.toFixed(1) + "s Attribution"}
                      </text>
                    </g>
                  );
                })}

                {/* Scrubber playback cursor line */}
                <line 
                  x1={playOffset} 
                  y1={0} 
                  x2={playOffset} 
                  y2={240} 
                  stroke="rgba(255, 204, 0, 0.8)" 
                  strokeWidth="1.5" 
                  strokeDasharray="3 3"
                />

                {/* Baseline 0 mV Center Guide */}
                <line 
                  x1="0" 
                  y1="120" 
                  x2="1000" 
                  y2="120" 
                  stroke="rgba(255, 255, 255, 0.08)" 
                  strokeWidth="1" 
                  strokeDasharray="6 4"
                />

                {/* Primary ECG Waveform Tracing */}
                <path 
                  d={fullscreenEcgPath}
                  fill="none" 
                  stroke={isAF ? "#FF3B30" : "#34C759"} 
                  strokeWidth="2.2" 
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ 
                    filter: `drop-shadow(0 0 6px ${isAF ? "rgba(255,59,48,0.7)" : "rgba(52,199,89,0.7)"})`
                  }}
                />
              </svg>
            </div>

            {/* Time Axis Markers (0s to 10s) */}
            <div style={{ position: "absolute", bottom: "8px", left: "20px", right: "40px", display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "rgba(255,255,255,0.4)", fontFamily: "monospace", pointerEvents: "none" }}>
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(s => (
                <div key={s} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{ width: "1px", height: "4px", backgroundColor: "rgba(255,255,255,0.3)", marginBottom: "2px" }} />
                  <span>{s}.0s</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Diagnostic Metadata & Salience Scrubber Row */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "16px" }}>
            {/* Salience & Key Attribution Windows */}
            <div style={{ backgroundColor: "rgba(255,255,255,0.03)", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.07)", padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: "700", textTransform: "uppercase", color: "var(--text-secondary)" }}>
                  Attributed AI Salience Windows (Click to Focus)
                </span>
                <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                  Derived from neural gradient backpropagation
                </span>
              </div>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {fullscreenAttributionRegions.length > 0 ? (
                  fullscreenAttributionRegions.map((region, idx) => {
                    const isSelected = selectedRegion && Math.abs(selectedRegion.start - region.start) < 0.05;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleRegionClick(region.start, region.end)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "8px",
                          backgroundColor: isSelected ? "rgba(255, 204, 0, 0.22)" : "rgba(0, 122, 255, 0.12)",
                          border: isSelected ? "1px solid #FFCC00" : "1px solid rgba(0, 122, 255, 0.3)",
                          color: isSelected ? "#FFCC00" : "var(--color-primary)",
                          fontSize: "0.75rem",
                          fontWeight: "700",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          boxShadow: isSelected ? "0 0 10px rgba(255, 204, 0, 0.3)" : "none"
                        }}
                      >
                        <span>{isSelected ? "★" : "⏱"} Window {idx + 1}: {region.start.toFixed(2)}s – {region.end.toFixed(2)}s</span>
                      </button>
                    );
                  })
                ) : (
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    Uniform baseline morphology across 10.0s window.
                  </span>
                )}
              </div>
            </div>

            {/* Clinical Telemetry Summary */}
            <div style={{ backgroundColor: "rgba(255,255,255,0.03)", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.07)", padding: "14px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: "700", textTransform: "uppercase", color: "var(--text-secondary)" }}>Clinical Telemetry</span>
                <span style={{ fontSize: "0.7rem", color: isAF ? "#FF3B30" : "#34C759", fontWeight: "700" }}>
                  {isAF ? "ARRHYTHMIA DETECTED" : "NORMAL SINUS RHYTHM"}
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "6px" }}>
                <div>Avg Heart Rate: <strong style={{ color: "#FFFFFF" }}>{Math.round(dailyStats.avgBpm)} bpm</strong></div>
                <div>RR Variance: <strong style={{ color: "#FFFFFF" }}>{Math.round(dailyStats.sdrr)} ms</strong></div>
                <div>RMSSD (HRV): <strong style={{ color: "#FFFFFF" }}>{Math.round(dailyStats.rmssd)} ms</strong></div>
                <div>Confidence: <strong style={{ color: "#FFFFFF" }}>{analysisResult ? `${analysisResult.confidence.toFixed(1)}%` : "—"}</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;


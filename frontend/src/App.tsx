import { useState, useEffect } from "react";
import { Outlet, NavLink } from "react-router-dom";
import "./App.css";
import { 
  Heart, Activity, ShieldCheck, LogOut, 
  Bell, User, TrendingUp, FileText, Battery, Sparkles, Database, Cpu 
} from "lucide-react";
import { auditFitData, verifyTelemetryConsistency } from "./services/fitSync";
import {
  subscribeToAuthChanges,
  loginWithEmail,
  registerWithEmail,
  loginWithGoogle,
  signOutUser,
  getUserToken,
} from "./services/auth";
import { getAppCheckToken } from "./services/appCheck";
import type { User as FirebaseUser } from "firebase/auth";

interface DataPoint {
  time: string;
  value: number;
}

interface DatasetStats {
  avgBpm: number;
  sdrr: number;
  rmssd: number;
}

export interface DatasetPayload {
  fileName: string;
  recordsCount: number;
  stats: DatasetStats;
  rows?: any[];
  rawSignal?: number[];
  file?: File | null;
  files?: File[];
  age?: number;
  sex?: number;
}

const METRIC_DATA_STREAMS: Record<string, DataPoint[]> = {
  heartRate: [],
  hrv: [
    { time: "08:00 AM", value: 42 },
    { time: "10:00 AM", value: 48 },
    { time: "12:00 PM", value: 45 },
    { time: "02:00 PM", value: 50 },
    { time: "04:00 PM", value: 41 },
    { time: "06:00 PM", value: 44 },
    { time: "08:00 PM", value: 46 },
  ],
  spo2: [
    { time: "08:00 AM", value: 98 },
    { time: "10:00 AM", value: 97 },
    { time: "12:00 PM", value: 99 },
    { time: "02:00 PM", value: 98 },
    { time: "04:00 PM", value: 98 },
    { time: "06:00 PM", value: 97 },
    { time: "08:00 PM", value: 99 },
  ],
  sleep: [
    { time: "Mon", value: 420 },
    { time: "Tue", value: 450 },
    { time: "Wed", value: 390 },
    { time: "Thu", value: 432 },
    { time: "Fri", value: 480 },
    { time: "Sat", value: 510 },
    { time: "Sun", value: 440 },
  ],
  steps: [
    { time: "08:00 AM", value: 1200 },
    { time: "10:00 AM", value: 2400 },
    { time: "12:00 PM", value: 3800 },
    { time: "02:00 PM", value: 4800 },
    { time: "04:00 PM", value: 5200 },
    { time: "06:00 PM", value: 5900 },
    { time: "08:00 PM", value: 6200 },
  ],
  calories: [
    { time: "08:00 AM", value: 80 },
    { time: "10:00 AM", value: 140 },
    { time: "12:00 PM", value: 210 },
    { time: "02:00 PM", value: 260 },
    { time: "04:00 PM", value: 290 },
    { time: "06:00 PM", value: 305 },
    { time: "08:00 PM", value: 320 },
  ],
  stress: [
    { time: "08:00 AM", value: 2 },
    { time: "10:00 AM", value: 4 },
    { time: "12:00 PM", value: 3 },
    { time: "02:00 PM", value: 5 },
    { time: "04:00 PM", value: 2 },
    { time: "06:00 PM", value: 1 },
    { time: "08:00 PM", value: 2 },
  ],
};

function App() {
  const [activeMetric, setActiveMetric] = useState<string>("heartRate");
  const [dataOrigin, setDataOrigin] = useState<"default" | "google_fit" | "csv">("default");
  const [isFitConnected, setIsFitConnected] = useState(false);
  const [uploadedDataset, setUploadedDataset] = useState<DatasetPayload | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Time ticker
  const [currentTime, setCurrentTime] = useState("");

  // ECG controls states
  const [isPlaying, setIsPlaying] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isFiltered, setIsFiltered] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Model selection state
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("default");
  
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
        const res = await fetch(`${apiUrl}/models`);
        if (res.ok) {
          const models = await res.json();
          setAvailableModels(models);
        }
      } catch (err) {
        console.error("Failed to fetch models", err);
      }
    };
    fetchModels();
  }, []);


  // AI predictions state
  const [analysisResult, setAnalysisResult] = useState<{
    resultType: string;
    confidence: number;
    stats: DatasetStats;
    modelVersion: string;
    explainableInsights: string[];
    explanationValues?: any[];
    inferenceTimeMs: number;
    probabilityVector?: number[];
    fileName?: string;
    highestRiskSegment?: number[];
    signalQuality?: string;
    comparisons?: any[];
  } | null>(null);

  // Daily dynamic stats loaded from backend or Google Fit
  const [dailyStats, setDailyStats] = useState({
    avgBpm: 70,
    sdrr: 55,
    rmssd: 45,
    steps: 8500,
    calories: 450,
    sleep: 7.8,
    stress: 1,
  });

  // Dynamic metric chart streams
  const [metricData, setMetricData] = useState<Record<string, DataPoint[]>>(METRIC_DATA_STREAMS);

  // Centralized Error Logger
  const logAppError = (context: string, error: any) => {
    console.error(`[CardioGuard Error] Context: ${context}`, error);
  };

  // Fetch metrics dynamically from backend API
  const fetchDashboardStats = async (currentUser: FirebaseUser | null) => {
    if (!currentUser) return;
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      if (appCheckToken) {
        headers["X-Firebase-App-Check"] = appCheckToken;
      }

      const response = await fetch(`${apiUrl}/analytics/daily`, {
        method: "GET",
        headers,
      });

      if (response.ok) {
        const data = await response.json();
        setDailyStats((prev) => ({
          ...prev,
          avgBpm: data.average_heart_rate || prev.avgBpm,
          sdrr: data.mean_sdrr_ms || prev.sdrr,
          rmssd: data.mean_rmssd_ms || prev.rmssd,
        }));
      }
    } catch (e) {
      logAppError("fetchDashboardStats", e);
    }
  };

  // Firebase Auth states
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((firebaseUser) => {
      setUser(firebaseUser);
      setAuthLoading(false);
      if (firebaseUser) {
        fetchDashboardStats(firebaseUser);
      }
    });
    return () => unsubscribe();
  }, []);

  const handleAuthAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      if (authMode === "login") {
        await loginWithEmail(emailInput, passwordInput);
      } else {
        await registerWithEmail(emailInput, passwordInput);
      }
      setEmailInput("");
      setPasswordInput("");
    } catch (err: any) {
      setAuthError(err.message || "Authentication failed.");
    }
  };

  const handleGoogleAuth = async () => {
    setAuthError(null);
    try {
      await loginWithGoogle();
    } catch (err: any) {
      setAuthError(err.message || "Google Sign-In failed.");
    }
  };

  const handleGoogleFitConnect = (syncedData: any[]) => {
    const audited = auditFitData(syncedData);
    
    const isConsistent = verifyTelemetryConsistency(
      { avgBpm: audited.avgBpm, steps: audited.steps },
      { avgBpm: audited.avgBpm, steps: audited.steps }
    );

    if (!isConsistent) {
      console.warn("[Telemetry] Consistency check failed. Requesting resync parameters.");
    }

    setIsFitConnected(true);
    setDataOrigin("google_fit");
    setUploadedDataset(null);
    setAnalysisResult(null);

    if (syncedData && syncedData.length > 0) {
      const formattedPoints = syncedData.map((d: any) => ({
        time: d.time,
        value: d.bpm || d.value
      }));
      setMetricData((prev) => ({
        ...prev,
        heartRate: formattedPoints
      }));
    }

    setDailyStats((prev) => ({
      ...prev,
      avgBpm: audited.avgBpm,
      steps: audited.steps,
      calories: audited.calories,
      sleep: audited.sleepMinutes / 60,
    }));
  };

  const handleGoogleFitDisconnect = () => {
    setIsFitConnected(false);
    setDataOrigin("default");
    setAnalysisResult(null);
    setMetricData(METRIC_DATA_STREAMS);
    setDailyStats({
      avgBpm: 72,
      sdrr: 45,
      rmssd: 32,
      steps: 6200,
      calories: 320,
      sleep: 7.2,
      stress: 2,
    });
  };

  const handleDatasetLoaded = (payload: DatasetPayload) => {
    setUploadedDataset(payload);
    setDataOrigin("csv");
    setIsFitConnected(false);
    setAnalysisResult(null);

    if (payload.rows && payload.rows.length > 0) {
      const sampled = payload.rows.slice(0, 15).map((row) => ({
        time: `${row.timeSec}s`,
        value: row.bpm
      }));
      setMetricData((prev) => ({
        ...prev,
        heartRate: sampled
      }));
    }

    setDailyStats((prev) => ({
      ...prev,
      avgBpm: payload.stats.avgBpm,
      sdrr: payload.stats.sdrr,
      rmssd: payload.stats.rmssd,
    }));
  };

  const handleClearDataset = () => {
    setUploadedDataset(null);
    setDataOrigin("default");
    setAnalysisResult(null);
    setMetricData(METRIC_DATA_STREAMS);
    setDailyStats({
      avgBpm: 72,
      sdrr: 45,
      rmssd: 32,
      steps: 6200,
      calories: 320,
      sleep: 7.2,
      stress: 2,
    });
  };

  const handleStartAnalysis = () => {
    setIsAnalyzing(true);
  };
  const handleResetAnalysis = () => {
    setAnalysisResult(null);
  };

  // Utility to calculate real BPM from the ECG waveform
  const extractHeartRateFromECG = (ecgData: number[], sampleRate: number = 100) => {
    if (!ecgData || ecgData.length === 0) return [];

    let max = -Infinity;
    for (let val of ecgData) if (val > max) max = val;

    const threshold = max * 0.6;
    const minDistance = Math.floor(sampleRate * 0.4); 

    const peaks: number[] = [];
    for (let i = 1; i < ecgData.length - 1; i++) {
        if (ecgData[i] > threshold && ecgData[i] > ecgData[i - 1] && ecgData[i] > ecgData[i + 1]) {
            if (peaks.length === 0 || (i - peaks[peaks.length - 1]) >= minDistance) {
                peaks.push(i);
            }
        }
    }

    const bpmData: DataPoint[] = [];
    for (let i = 1; i < peaks.length; i++) {
        const rrSamples = peaks[i] - peaks[i - 1];
        const rrSeconds = rrSamples / sampleRate;
        const bpm = Math.round(60 / rrSeconds);
        const timeSec = (peaks[i] / sampleRate).toFixed(2);
        bpmData.push({ time: `${timeSec}s`, value: bpm });
    }

    return bpmData;
  };

  const handleAnalysisComplete = async () => {
    if (!uploadedDataset && dataOrigin === "csv") return;
    setIsAnalyzing(true);

    let activeStats: DatasetStats = {
      avgBpm: dailyStats.avgBpm,
      sdrr: dailyStats.sdrr,
      rmssd: dailyStats.rmssd,
    };

    let resultType: string = "Normal Sinus Rhythm";
    let confidence = 0;
    let modelVersion = "Unknown";
    let explainableInsights: string[] = [];
    let explanationValues: any[] = [];
    let inferenceTimeMs = 0;
    let probabilityVector: number[] = [];
    let highestRiskSegment: number[] | undefined = undefined;
    let signalQuality: string | undefined = undefined;
    let comparisons: any[] | undefined = undefined;

    if (dataOrigin === "csv" && uploadedDataset) {
      activeStats = uploadedDataset.stats;
    }

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

      let response: Response;
      if (dataOrigin === "csv" && (uploadedDataset?.file || (uploadedDataset?.files && uploadedDataset.files.length > 0))) {
        // Real ECG upload using multipart/form-data
        const formData = new FormData();
        
        if (uploadedDataset.files && uploadedDataset.files.length > 0) {
            uploadedDataset.files.forEach((f: File) => formData.append("files", f));
        } else if (uploadedDataset.file) {
            formData.append("files", uploadedDataset.file);
        }
        
        formData.append("age", uploadedDataset.age !== undefined ? uploadedDataset.age.toString() : "30");
        formData.append("sex", uploadedDataset.sex !== undefined ? uploadedDataset.sex.toString() : "0");

        // Do not set Content-Type for FormData, browser sets it with boundary
        const formDataHeaders: Record<string, string> = { ...headers };
        delete formDataHeaders["Content-Type"];

        if (selectedModelId === "compare") {
            const enabledIds = availableModels.map((m: any) => m.id).join(",");
            formData.append("model_ids", enabledIds);
            response = await fetch(`${apiUrl}/predictions/physionet/compare`, {
              method: "POST",
              headers: formDataHeaders,
              body: formData,
            });
        } else {
            if (selectedModelId !== "default") {
              formData.append("model_id", selectedModelId);
            }
            response = await fetch(`${apiUrl}/predictions/physionet`, {
              method: "POST",
              headers: formDataHeaders,
              body: formData,
            });
        }
      } else {
        // Fallback for mock/manual entry
        const payload: any = {
          avg_bpm: activeStats.avgBpm,
          sdrr_ms: activeStats.sdrr,
          rmssd_ms: activeStats.rmssd,
          age: uploadedDataset?.age !== undefined ? uploadedDataset.age : 30,
          sex: uploadedDataset?.sex !== undefined ? uploadedDataset.sex : 0
        };
        
        if (selectedModelId === "compare") {
            const enabledIds = availableModels.map((m: any) => m.id).join(",");
            payload.model_ids = enabledIds;
        } else if (selectedModelId !== "default") {
            payload.model_id = selectedModelId;
        }

        if (dataOrigin === "csv" && uploadedDataset?.rawSignal) {
          payload.raw_ecg = uploadedDataset.rawSignal;
          payload.fs = 100.0;
        }

        const endpoint = selectedModelId === "compare" ? "/predictions/compare" : "/prediction";
        response = await fetch(`${apiUrl}${endpoint}`, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        });
      }

      if (response.ok) {
        const data = await response.json();
        
        comparisons = undefined;
        
        if (data.comparisons) {
            comparisons = data.comparisons;
            // set main view to first successful model or generic overview
            resultType = "Multi-Model Comparison";
            confidence = 100;
            modelVersion = "Ensemble Mode";
        } else if (data.prediction && data.prediction.label) {
            resultType = data.prediction.label || "Unknown";
            confidence = data.prediction.confidence ?? 0;
            modelVersion = data.model_version || "Unknown";
            explainableInsights = data.explanation?.values?.map((v: any) => {
               if (typeof v === 'string') return v;
               let parsedTime = v.feature;
               if (v.feature && v.feature.startsWith('time_')) {
                 const sampleIdx = parseInt(v.feature.split('_')[1], 10);
                 if (!isNaN(sampleIdx)) {
                   parsedTime = `Time ${(sampleIdx / 100).toFixed(2)}s`;
                 }
               }
               return `${parsedTime} impact: ${(v.contribution > 0 ? '+' : '')}${(v.contribution * 100).toFixed(1)}%`;
            }) || explainableInsights;
            inferenceTimeMs = data.inference_time_ms || 32;
            const rawVector = data.class_probabilities ? 
              [data.class_probabilities.Normal, data.class_probabilities.AFIB, data.class_probabilities["Conduction Block"], data.class_probabilities["Other Arrhythmia"]] : [];
            // API returns percentages (0-100), we need decimals (0-1)
            probabilityVector = rawVector.map(v => Math.max(0, Math.min(1, (v || 0) / 100.0)));
            highestRiskSegment = data.highest_risk_segment || [];
            signalQuality = data.signal_quality || "UNKNOWN";
            explanationValues = data.explanation?.values || [];
            if (data.hr_bpm) activeStats.avgBpm = Math.round(data.hr_bpm);
            if (data.rmssd_ms) activeStats.rmssd = Math.round(data.rmssd_ms);
        } else {
            resultType = data.classification || "Unknown";
            confidence = data.confidence_score ?? 0;
            modelVersion = data.model_version || modelVersion;
            explainableInsights = data.explainable_insights || explainableInsights;
            inferenceTimeMs = data.inference_time_ms || 32;
            const rawLegacy = data.probability_vector || [];
            probabilityVector = rawLegacy.map((v: number) => Math.max(0, Math.min(1, v)));
            highestRiskSegment = data.highest_risk_segment;
            signalQuality = data.signal_quality;
            explanationValues = data.explanation?.values || [];
        }
        await fetchDashboardStats(user);
      } else {
        let errorDetail = "Backend offline";
        try {
            const errData = await response.json();
            errorDetail = errData.detail || errorDetail;
        } catch (jsonErr) {
            // unable to parse JSON error
        }
        throw new Error(errorDetail);
      }
    } catch (e: any) {
      logAppError("Detection API", e);
      resultType = "normal";
      confidence = 0;
      explainableInsights = [e.message || "Failed to communicate with prediction service."];
      explanationValues = [];
    }
    if (highestRiskSegment && highestRiskSegment.length > 0) {
      const derivedBpm = extractHeartRateFromECG(highestRiskSegment, 100);
      setMetricData((prev) => ({ ...prev, heartRate: derivedBpm }));
    }

    setIsAnalyzing(false);
    setAnalysisResult({ 
      resultType, 
      confidence, 
      stats: activeStats, 
      modelVersion, 
      explainableInsights,
      explanationValues,
      inferenceTimeMs,
      probabilityVector,
      fileName: uploadedDataset?.fileName,
      highestRiskSegment,
      signalQuality,
      comparisons
    });
  };

  const isAF = analysisResult?.resultType === "AFIB" || analysisResult?.resultType === "Conduction Block" || analysisResult?.resultType === "Other Arrhythmia";

  if (authLoading) {
    return (
      <div className="app-container" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="glass-panel" style={{ padding: "40px", textAlign: "center" }}>
          <div className="heartbeat-animation" style={{ width: "50px", height: "50px", borderRadius: "50%", background: "linear-gradient(135deg, var(--color-primary), var(--color-secondary))", margin: "0 auto 20px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Heart size={24} color="#FFFFFF" fill="#FFFFFF" />
          </div>
          <p style={{ color: "#FFFFFF", fontSize: "0.9rem" }}>Loading CardioGuard AI...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app-container" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "20px" }}>
        <div className="glass-panel" style={{ maxWidth: "400px", width: "100%", padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
          <div style={{ textAlign: "center" }}>
            <div className="heartbeat-animation" style={{ width: "48px", height: "48px", borderRadius: "50%", background: "linear-gradient(135deg, var(--color-primary), var(--color-secondary))", margin: "0 auto 16px", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Heart size={24} color="#FFFFFF" fill="#FFFFFF" />
            </div>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "800", color: "#FFFFFF" }}>CardioGuard AI</h2>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "4px" }}>
              Premium Health Monitoring & Sync
            </p>
          </div>

          <form onSubmit={handleAuthAction} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Email Address</label>
              <input
                type="email"
                required
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                style={{ width: "100%", padding: "10px 14px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255, 255, 255, 0.05)", color: "#FFFFFF", fontSize: "0.85rem" }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Password</label>
              <input
                type="password"
                required
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                style={{ width: "100%", padding: "10px 14px", borderRadius: "8px", border: "1px solid var(--border-glass)", backgroundColor: "rgba(255, 255, 255, 0.05)", color: "#FFFFFF", fontSize: "0.85rem" }}
              />
            </div>

            {authError && (
              <p style={{ color: "var(--color-risk)", fontSize: "0.75rem", margin: 0 }}>{authError}</p>
            )}

            <button type="submit" className="btn-primary" style={{ width: "100%", justifyContent: "center", padding: "10px" }}>
              {authMode === "login" ? "Sign In" : "Sign Up"}
            </button>
          </form>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <button onClick={handleGoogleAuth} className="btn-secondary" style={{ width: "100%", justifyContent: "center", padding: "10px" }}>
              Continue with Google
            </button>
            <p style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              {authMode === "login" ? "Don't have an account? " : "Already have an account? "}
              <span
                onClick={() => setAuthMode(authMode === "login" ? "signup" : "login")}
                style={{ color: "var(--color-secondary)", cursor: "pointer", fontWeight: "600" }}
              >
                {authMode === "login" ? "Sign Up" : "Sign In"}
              </span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const contextValue = {
    activeMetric,
    setActiveMetric,
    dataOrigin,
    setDataOrigin,
    isFitConnected,
    setIsFitConnected,
    uploadedDataset,
    setUploadedDataset,
    isAnalyzing,
    setIsAnalyzing,
    analysisResult,
    setAnalysisResult,
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
    availableModels,
    selectedModelId,
    setSelectedModelId,
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
    user,
  };

  return (
    <div className="app-container">
      
      {/* Sticky Collapsible Desktop Sidebar */}
      <aside className="desktop-sidebar">
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "linear-gradient(135deg, var(--color-primary), var(--color-secondary))", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <Heart size={16} color="#FFFFFF" fill="#FFFFFF" />
          </div>
          <span className="logo-text" style={{ fontSize: "1.1rem", fontWeight: "800", color: "#FFFFFF" }}>CardioGuard</span>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%" }}>
          <NavLink to="/dashboard" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Activity size={18} />
            <span className="nav-label">Dashboard</span>
          </NavLink>
          <NavLink to="/trends" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <TrendingUp size={18} />
            <span className="nav-label">Trends</span>
          </NavLink>
          <NavLink to="/reports" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <FileText size={18} />
            <span className="nav-label">Reports</span>
          </NavLink>
          <NavLink to="/notifications" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Bell size={18} />
            <span className="nav-label">Notifications</span>
          </NavLink>
          <NavLink to="/connections" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Heart size={18} />
            <span className="nav-label">Connections</span>
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <ShieldCheck size={18} />
            <span className="nav-label">Settings</span>
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <User size={18} />
            <span className="nav-label">Profile</span>
          </NavLink>
          <NavLink to="/coach" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Sparkles size={18} />
            <span className="nav-label">AI Coach</span>
          </NavLink>
          <NavLink to="/doctor" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <ShieldCheck size={18} />
            <span className="nav-label">Doctor Portal</span>
          </NavLink>
          <NavLink to="/devices" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Battery size={18} />
            <span className="nav-label">Connected Devices</span>
          </NavLink>
          <NavLink to="/sync-center" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Database size={18} />
            <span className="nav-label">Sync Center</span>
          </NavLink>
          <NavLink to="/privacy" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <User size={18} />
            <span className="nav-label">Privacy Center</span>
          </NavLink>
          <NavLink to="/explainability" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Cpu size={18} />
            <span className="nav-label">Explainability</span>
          </NavLink>
          <NavLink to="/model-registry" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <FileText size={18} />
            <span className="nav-label">Model Registry</span>
          </NavLink>
          <NavLink to="/dataset-manager" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Database size={18} />
            <span className="nav-label">Dataset Manager</span>
          </NavLink>
          <NavLink to="/system-monitoring" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <Cpu size={18} />
            <span className="nav-label">System Monitoring</span>
          </NavLink>
          <NavLink to="/research" className={({ isActive }) => `btn-secondary ${isActive ? "active" : ""}`}>
            <TrendingUp size={18} />
            <span className="nav-label">Research Mode</span>
          </NavLink>
        </nav>

        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
          <div className="user-info" style={{ alignItems: "center", gap: "10px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "50%", backgroundColor: "rgba(255,255,255,0.05)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <User size={16} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: "600", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>{user.email}</span>
              <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>Premium Account</span>
            </div>
          </div>
          <button onClick={signOutUser} className="btn-secondary" style={{ width: "100%", padding: "8px", justifyContent: "center" }}>
            <LogOut size={14} />
          </button>
        </div>
      </aside>

      {/* Main Workspace Column */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflowY: "auto", position: "relative" }}>
        
        {/* Apple HIG Clean Header Row */}
        <header style={{ borderBottom: "1px solid var(--border-glass)", padding: "12px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(9, 9, 15, 0.8)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 99 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <span style={{ fontSize: "1.15rem", fontWeight: "800" }}>{currentTime}</span>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", padding: "4px 8px", borderRadius: "12px", backgroundColor: "rgba(52, 199, 89, 0.08)", border: "1px solid rgba(52, 199, 89, 0.2)" }}>
              <ShieldCheck size={12} style={{ color: "var(--color-normal)" }} />
              <span style={{ fontSize: "0.65rem", fontWeight: "600", color: "var(--color-normal)" }}>Vitals Active</span>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <Battery size={14} color="#34C759" />
              <span>88%</span>
            </div>
            <span>Connected: Apple Watch Ultra</span>
            <button className="btn-secondary" style={{ padding: "6px", borderRadius: "50%" }}>
              <Bell size={14} />
            </button>
          </div>
        </header>

        {/* Dynamic Nested Page Content Area */}
        <main style={{ padding: "24px", flex: 1, minHeight: 0 }}>
          {/* Global Clinical Disclaimer Banner */}
          <div style={{ 
            marginBottom: "20px", 
            padding: "10px 16px", 
            borderRadius: "8px", 
            backgroundColor: "rgba(255, 149, 0, 0.05)", 
            border: "1px solid rgba(255, 149, 0, 0.15)", 
            fontSize: "0.68rem", 
            color: "var(--text-secondary)", 
            lineHeight: "1.4" 
          }}>
            <span style={{ fontWeight: "700", color: "#FFFFFF" }}>Global Disclaimer:</span> CardioGuard AI is intended for research, educational, and wellness support. It does not replace professional medical advice, diagnosis, or clinical evaluation.
          </div>
          <Outlet context={contextValue} />
        </main>

      </div>

      {/* Apple-style sticky mobile bottom navigation bar */}
      <div className="mobile-bottom-bar" style={{ display: "none", position: "fixed", bottom: 0, left: 0, right: 0, height: "60px", borderTop: "1px solid var(--border-glass)", background: "rgba(19, 21, 26, 0.9)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", justifyContent: "space-around", alignItems: "center", zIndex: 100 }}>
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? "active" : ""}>
          <Activity size={18} />
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/trends" className={({ isActive }) => isActive ? "active" : ""}>
          <TrendingUp size={18} />
          <span>Trends</span>
        </NavLink>
        <NavLink to="/reports" className={({ isActive }) => isActive ? "active" : ""}>
          <FileText size={18} />
          <span>Reports</span>
        </NavLink>
      </div>

    </div>
  );
}

export default App;

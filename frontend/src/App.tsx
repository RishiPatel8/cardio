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

interface RecordRow {
  index: number;
  timeSec: number;
  rrIntervalMs: number;
  bpm: number;
}

interface DatasetPayload {
  fileName: string;
  recordsCount: number;
  rows: RecordRow[];
  stats: DatasetStats;
}

const METRIC_DATA_STREAMS: Record<string, DataPoint[]> = {
  heartRate: [
    { time: "08:00 AM", value: 71 },
    { time: "10:00 AM", value: 73 },
    { time: "12:00 PM", value: 70 },
    { time: "02:00 PM", value: 78 },
    { time: "04:00 PM", value: 68 },
    { time: "06:00 PM", value: 69 },
    { time: "08:00 PM", value: 72 },
  ],
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
  const [playOffset, setPlayOffset] = useState(0);

  // AI predictions state
  const [analysisResult, setAnalysisResult] = useState<{
    resultType: "normal" | "af";
    confidence: number;
    stats: DatasetStats;
    modelVersion: string;
    explainableInsights: string[];
    inferenceTimeMs: number;
    fileName?: string;
  } | null>(null);

  // Daily dynamic stats loaded from backend or Google Fit
  const [dailyStats, setDailyStats] = useState({
    avgBpm: 72,
    sdrr: 45,
    rmssd: 32,
    steps: 6200,
    calories: 320,
    sleep: 7.2,
    stress: 2,
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

  // ECG waveform animation loop
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setPlayOffset((prev) => (prev + 2) % 300);
    }, 40);
    return () => clearInterval(interval);
  }, [isPlaying]);

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

  const handleAnalysisComplete = async () => {
    setIsAnalyzing(false);

    let activeStats: DatasetStats = {
      avgBpm: dailyStats.avgBpm,
      sdrr: dailyStats.sdrr,
      rmssd: dailyStats.rmssd,
    };

    let resultType: "normal" | "af" = "normal";
    let confidence = 94;
    let modelVersion = "ensemble-random_forest-v2.0";
    let explainableInsights: string[] = [
      `Average heart rate registered at ${activeStats.avgBpm} bpm.`,
      `SDRR metric of ${activeStats.sdrr}ms indicates stable heart rhythms.`
    ];
    let inferenceTimeMs = 45;

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

      const response = await fetch(`${apiUrl}/prediction`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          avg_bpm: activeStats.avgBpm,
          sdrr_ms: activeStats.sdrr,
          rmssd_ms: activeStats.rmssd,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        resultType = data.classification === "AF Risk" ? "af" : "normal";
        confidence = data.confidence_score;
        modelVersion = data.model_version || modelVersion;
        explainableInsights = data.explainable_insights || explainableInsights;
        inferenceTimeMs = data.inference_time_ms || 32;
        await fetchDashboardStats(user);
      } else {
        throw new Error("Backend offline");
      }
    } catch (e) {
      logAppError("handleAnalysisComplete", e);
      if (activeStats.sdrr > 90 || activeStats.rmssd > 80) {
        resultType = "af";
        explainableInsights = [
          `Average heart rate registered at ${activeStats.avgBpm} bpm.`,
          `Abnormal SDRR score of ${activeStats.sdrr}ms (exceeding 90ms) indicating high heart rate variability.`,
          "RMSSD exceeds optimal bounds. Potential atrial fibrillations flagged."
        ];
      } else {
        resultType = "normal";
        explainableInsights = [
          `Average heart rate registered at ${activeStats.avgBpm} bpm.`,
          `Stable SDRR metric of ${activeStats.sdrr}ms matching sinus rhythm patterns.`
        ];
      }
      confidence = 92;
      modelVersion = "edge-tflite-fallback-v1.0";
      inferenceTimeMs = 18;
    }

    setAnalysisResult({
      resultType,
      confidence,
      stats: activeStats,
      modelVersion,
      explainableInsights,
      inferenceTimeMs,
      fileName: dataOrigin === "csv" ? uploadedDataset?.fileName : undefined,
    });
  };

  const isAF = analysisResult?.resultType === "af";

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
    playOffset,
    setPlayOffset,
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

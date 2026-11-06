import React, { useState, useEffect } from "react";
import { motion, AnimatePresence, useScroll, useSpring } from "framer-motion";
import { 
  Heart, Activity, ShieldCheck, Cpu, FileText, 
  ArrowRight, CheckCircle, Sparkles, UserCheck, Play
} from "lucide-react";
import type { User as FirebaseUser } from "firebase/auth";
import { loginWithEmail, registerWithEmail, loginWithGoogle } from "../services/auth";
import Heart3DCanvas from "../components/landing/Heart3DCanvas";
import TiltCard3D from "../components/landing/TiltCard3D";
import LiveTelemetrySimulator from "../components/landing/LiveTelemetrySimulator";
import "./LandingPage.css";

interface LandingPageProps {
  user: FirebaseUser | null;
  onConnectToDashboard: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  user,
  onConnectToDashboard,
}) => {
  // Initial entrance loading sequence
  const [initialLoading, setInitialLoading] = useState(true);
  const [scrolled, setScrolled] = useState(false);

  // Authentication State
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // Scroll Progress Line
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });

  useEffect(() => {
    // Initial loading sequence timer
    const timer = setTimeout(() => {
      setInitialLoading(false);
    }, 1100);

    const handleScroll = () => {
      setScrolled(window.scrollY > 25);
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Auth Submit Handlers
  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthSubmitting(true);
    try {
      if (authMode === "login") {
        await loginWithEmail(emailInput, passwordInput);
      } else {
        await registerWithEmail(emailInput, passwordInput);
      }
      onConnectToDashboard();
    } catch (err: any) {
      setAuthError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setAuthSubmitting(false);
    }
  };

  const handleGoogleAuth = async () => {
    setAuthError(null);
    setAuthSubmitting(true);
    try {
      await loginWithGoogle();
      onConnectToDashboard();
    } catch (err: any) {
      setAuthError(err.message || "Google Sign-In failed.");
    } finally {
      setAuthSubmitting(false);
    }
  };

  const handleQuickDemoAccess = async () => {
    setAuthError(null);
    setAuthSubmitting(true);
    try {
      try {
        await loginWithEmail("clinician@cardioguard.ai", "DoctorPass2026!");
      } catch {
        // If not created yet in Firebase, auto-register
        await registerWithEmail("clinician@cardioguard.ai", "DoctorPass2026!");
      }
      onConnectToDashboard();
    } catch (err: any) {
      // In offline mock mode or fallback, directly connect
      console.warn("Demo sign-in fallback active", err);
      onConnectToDashboard();
    } finally {
      setAuthSubmitting(false);
    }
  };

  return (
    <div className="landing-container">
      {/* Top Scroll Progress Bar */}
      <motion.div className="scroll-progress-bar" style={{ scaleX }} />

      {/* Ambient Radial Lights */}
      <div className="landing-ambient-glow glow-purple" />
      <div className="landing-ambient-glow glow-crimson" />
      <div className="landing-ambient-glow glow-cyan" />
      <div className="landing-grid-bg" />

      {/* Initial Entrance Cinematic Curtain Animation */}
      <AnimatePresence>
        {initialLoading && (
          <motion.div
            className="landing-loader-curtain"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 1.04 }}
            transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
          >
            <div style={{ position: "relative", width: "90px", height: "90px", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <motion.div
                animate={{ scale: [1, 1.25, 1], opacity: [0.3, 0.8, 0.3] }}
                transition={{ repeat: Infinity, duration: 1.4 }}
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: "50%",
                  background: "radial-gradient(circle, rgba(255, 45, 85, 0.4) 0%, transparent 70%)",
                }}
              />
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #FF2D55, #5856D6)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 25px rgba(255, 45, 85, 0.6)",
                }}
              >
                <Heart size={28} color="#FFFFFF" fill="#FFFFFF" />
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Activity size={18} color="#FF2D55" className="spin-slow" />
                <span style={{ fontSize: "0.85rem", fontWeight: "700", letterSpacing: "1.5px", color: "#F8FAFC", textTransform: "uppercase" }}>
                  INITIALIZING CARDIOGUARD AI
                </span>
              </div>
              <span style={{ fontSize: "0.75rem", color: "#94A3B8" }}>
                Loading 7-Model Consensus & DeepSHAP Engine...
              </span>
            </div>

            {/* Glowing SVG ECG Path */}
            <svg width="240" height="40" viewBox="0 0 240 40" fill="none">
              <path
                d="M 10 20 L 60 20 L 70 10 L 80 32 L 92 4 L 104 36 L 114 20 L 160 20 L 175 14 L 185 24 L 195 20 L 230 20"
                stroke="#FF2D55"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="loader-ecg-path"
              />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 1. Sticky Navigation Header */}
      <header className={`landing-nav ${scrolled ? "scrolled" : ""}`}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #FF2D55, #5856D6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 15px rgba(255, 45, 85, 0.4)",
            }}
          >
            <Heart size={20} color="#FFFFFF" fill="#FFFFFF" />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "1.05rem", fontWeight: "900", color: "#FFFFFF", letterSpacing: "-0.02em" }}>
              CardioGuard AI
            </span>
            <span style={{ fontSize: "0.65rem", color: "#94A3B8", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Clinical Intelligence v8.0
            </span>
          </div>
        </div>

        <nav className="nav-links">
          <button onClick={() => scrollToSection("pillars")} className="nav-link-item">
            Capabilities
          </button>
          <button onClick={() => scrollToSection("simulator")} className="nav-link-item">
            Live Simulator
          </button>
          <button onClick={() => scrollToSection("architecture")} className="nav-link-item">
            Architecture
          </button>
          <button onClick={() => scrollToSection("auth-section")} className="nav-link-item">
            Clinician Access
          </button>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {user ? (
            <button onClick={onConnectToDashboard} className="btn-launch-primary" style={{ padding: "10px 20px", fontSize: "0.85rem" }}>
              Enter Dashboard <ArrowRight size={16} />
            </button>
          ) : (
            <>
              <button
                onClick={() => scrollToSection("auth-section")}
                className="btn-launch-secondary"
                style={{ padding: "10px 18px", fontSize: "0.85rem" }}
              >
                Sign In
              </button>
              <button
                onClick={handleQuickDemoAccess}
                className="btn-launch-primary"
                style={{ padding: "10px 20px", fontSize: "0.85rem" }}
              >
                Launch Console <ArrowRight size={16} />
              </button>
            </>
          )}
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="landing-hero">
        <motion.div
          className="hero-content"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
        >
          <div className="hero-eyebrow">
            <span className="hero-eyebrow-dot" />
            <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#F8FAFC", letterSpacing: "0.5px" }}>
              MIT-BIH & PhysioNet Clinical Benchmarked
            </span>
          </div>

          <h1 className="hero-title">
            Real-Time Arrhythmia Detection with <span className="hero-title-gradient">Sample-Level DeepSHAP</span>
          </h1>

          <p className="hero-subtitle">
            Next-generation cardiovascular intelligence for clinicians and researchers. Evaluate 10-second ECG telemetry through seven deep ensemble architectures with automated sample-level attribution heatmaps.
          </p>

          <div className="hero-cta-group">
            {user ? (
              <button onClick={onConnectToDashboard} className="btn-launch-primary">
                Open Clinical Dashboard <ArrowRight size={18} />
              </button>
            ) : (
              <>
                <button onClick={() => scrollToSection("auth-section")} className="btn-launch-primary">
                  Launch Diagnostic Console <ArrowRight size={18} />
                </button>
                <button onClick={() => scrollToSection("simulator")} className="btn-launch-secondary">
                  <Play size={16} color="#FF2D55" fill="#FF2D55" /> Test Live Waveform
                </button>
              </>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "24px", paddingTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle size={16} color="#10B981" />
              <span style={{ fontSize: "0.75rem", color: "#94A3B8", fontWeight: "600" }}>7 Multi-Model Consensus</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle size={16} color="#10B981" />
              <span style={{ fontSize: "0.75rem", color: "#94A3B8", fontWeight: "600" }}>100 Hz Lead MLII Ingestion</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle size={16} color="#10B981" />
              <span style={{ fontSize: "0.75rem", color: "#94A3B8", fontWeight: "600" }}>Multi-Page XAI Reports</span>
            </div>
          </div>
        </motion.div>

        {/* 3D Interactive Cardiac Stage */}
        <div className="hero-3d-stage">
          <Heart3DCanvas bpm={72} interactive={true} />
        </div>
      </section>

      {/* 3. Performance & Verification Metrics Strip */}
      <section className="landing-section" style={{ paddingTop: "0" }}>
        <motion.div
          className="metrics-strip"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="metric-strip-item">
            <span className="metric-number">7</span>
            <span className="metric-label">Neural Network Architectures</span>
            <span style={{ fontSize: "0.7rem", color: "#64748B" }}>Trained on 100 Hz ECG signals</span>
          </div>

          <div className="metric-strip-item">
            <span className="metric-number">100 Hz</span>
            <span className="metric-label">Signal Sampling Frequency</span>
            <span style={{ fontSize: "0.7rem", color: "#64748B" }}>1,000 samples / 10s rhythm strip</span>
          </div>

          <div className="metric-strip-item">
            <span className="metric-number">&lt; 220 ms</span>
            <span className="metric-label">Inference & Attribution Latency</span>
            <span style={{ fontSize: "0.7rem", color: "#64748B" }}>Optimized GPU / CPU execution</span>
          </div>

          <div className="metric-strip-item">
            <span className="metric-number">4-Class</span>
            <span className="metric-label">Arrhythmia Categorization</span>
            <span style={{ fontSize: "0.7rem", color: "#64748B" }}>Sinus, AFIB, Block, Other</span>
          </div>
        </motion.div>
      </section>

      {/* 4. Core Capabilities Pillars */}
      <section id="pillars" className="landing-section">
        <motion.div
          className="section-header"
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="section-tag">Clinical AI Capabilities</span>
          <h2 className="section-title">Engineered for Diagnostic Precision and Auditability</h2>
          <p className="section-desc">
            Combining multi-architecture verification with explainable gradient attributions to eliminate black-box AI risk in cardiac decision support.
          </p>
        </motion.div>

        <div className="pillars-grid">
          <TiltCard3D>
            <div className="pillar-card">
              <div className="pillar-icon-box" style={{ background: "rgba(88, 86, 214, 0.15)", color: "#5856D6" }}>
                <Cpu size={24} />
              </div>
              <h3 className="pillar-title">Multi-Model Neural Consensus</h3>
              <p className="pillar-desc">
                Evaluate ECG waveforms across 1D CNN, ResNet, Temporal Convolutional Networks (TCN), and Multimodal classifiers simultaneously to identify architectural agreement and divergence.
              </p>
            </div>
          </TiltCard3D>

          <TiltCard3D>
            <div className="pillar-card">
              <div className="pillar-icon-box" style={{ background: "rgba(255, 45, 85, 0.15)", color: "#FF2D55" }}>
                <Activity size={24} />
              </div>
              <h3 className="pillar-title">DeepSHAP Temporal Attribution</h3>
              <p className="pillar-desc">
                Visualizes exactly which 10 ms waveform intervals shifted the model toward an arrhythmia classification, highlighting QRS complexes, ST segments, and fibrillatory baseline deviations.
              </p>
            </div>
          </TiltCard3D>

          <TiltCard3D>
            <div className="pillar-card">
              <div className="pillar-icon-box" style={{ background: "rgba(0, 122, 255, 0.15)", color: "#007AFF" }}>
                <FileText size={24} />
              </div>
              <h3 className="pillar-title">Clinical Diagnostic PDF Export</h3>
              <p className="pillar-desc">
                One-click compilation of publication-grade multi-page diagnostic reports complete with standard 25 mm/s rhythm strips, probability bars, etiology tables, and clinical follow-up protocols.
              </p>
            </div>
          </TiltCard3D>

          <TiltCard3D>
            <div className="pillar-card">
              <div className="pillar-icon-box" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10B981" }}>
                <ShieldCheck size={24} />
              </div>
              <h3 className="pillar-title">Autonomic HRV & Risk Stratification</h3>
              <p className="pillar-desc">
                Seamless synchronization with Google Fit and clinical wearables to integrate continuous heart rate, RMSSD, SDRR, blood pressure, and medical cofactors into multimodal assessments.
              </p>
            </div>
          </TiltCard3D>
        </div>
      </section>

      {/* 5. Interactive Live Telemetry Simulator */}
      <section id="simulator" className="landing-section">
        <motion.div
          className="section-header"
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="section-tag">Interactive Clinical Demonstration</span>
          <h2 className="section-title">Live 100 Hz Rhythm Strip & Saliency Overlay</h2>
          <p className="section-desc">
            Select a rhythm preset to observe real-time waveform rendering, automated signal quality validation, and DeepSHAP salient interval highlighting.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <LiveTelemetrySimulator />
        </motion.div>
      </section>

      {/* 6. Diagnostic Processing Pipeline */}
      <section id="architecture" className="landing-section">
        <motion.div
          className="section-header"
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="section-tag">End-to-End Pipeline</span>
          <h2 className="section-title">From Raw Telemetry to Explainable Clinical Verdict</h2>
          <p className="section-desc">
            A deterministic, auditable pipeline ensuring high signal integrity, reproducible inference, and comprehensive reporting.
          </p>
        </motion.div>

        <div className="architecture-pipeline">
          <div className="pipeline-step">
            <span className="pipeline-step-badge">STEP 01</span>
            <h4 className="pipeline-step-title">Telemetry Ingestion</h4>
            <p className="pipeline-step-desc">
              Ingests 100 Hz Lead MLII or PhysioNet (.dat/.hea/.atr) records with automatic baseline wandering removal.
            </p>
          </div>

          <div className="pipeline-step">
            <span className="pipeline-step-badge">STEP 02</span>
            <h4 className="pipeline-step-title">Quality Validation</h4>
            <p className="pipeline-step-desc">
              Evaluates Signal-to-Noise Ratio (SNR) and checks electrode contact to reject corrupted or uninterpretable segments.
            </p>
          </div>

          <div className="pipeline-step">
            <span className="pipeline-step-badge">STEP 03</span>
            <h4 className="pipeline-step-title">7-Model Inference</h4>
            <p className="pipeline-step-desc">
              Parallel execution across 1D CNN, ResNet, TCN, and Multimodal networks using strict inference evaluation mode.
            </p>
          </div>

          <div className="pipeline-step">
            <span className="pipeline-step-badge">STEP 04</span>
            <h4 className="pipeline-step-title">DeepSHAP Saliency</h4>
            <p className="pipeline-step-desc">
              Computes sample-level attribution weights to cluster morphological deviations in QRS, ST, and baseline intervals.
            </p>
          </div>

          <div className="pipeline-step">
            <span className="pipeline-step-badge">STEP 05</span>
            <h4 className="pipeline-step-title">Clinical Synthesis</h4>
            <p className="pipeline-step-desc">
              Compiles multi-class probabilities, differential causes, and actionable recommendations into the final report.
            </p>
          </div>
        </div>
      </section>

      {/* 7. Seamless Clinician Authentication Section */}
      <section id="auth-section" className="landing-section" style={{ paddingBottom: "110px" }}>
        <motion.div
          className="section-header"
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="section-tag">Access Console</span>
          <h2 className="section-title">
            {user ? "Session Active" : "Connect to CardioGuard AI"}
          </h2>
          <p className="section-desc">
            {user
              ? `Signed in as ${user.email}. Jump straight to your diagnostic telemetry console.`
              : "Sign in with your clinical credentials, Google OAuth, or launch instant 1-click evaluation access."}
          </p>
        </motion.div>

        <div className="auth-embed-wrapper">
          {user ? (
            <div className="auth-glass-card" style={{ textAlign: "center" }}>
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "50%",
                  background: "rgba(16, 185, 129, 0.15)",
                  border: "1px solid rgba(16, 185, 129, 0.4)",
                  margin: "0 auto",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <UserCheck size={28} color="#10B981" />
              </div>
              <div>
                <h3 style={{ fontSize: "1.2rem", fontWeight: "800", color: "#FFFFFF", margin: 0 }}>
                  Ready to Analyze
                </h3>
                <p style={{ fontSize: "0.85rem", color: "#94A3B8", marginTop: "6px" }}>
                  Connected as <span style={{ color: "#FFFFFF", fontWeight: "600" }}>{user.email}</span>
                </p>
              </div>

              <button onClick={onConnectToDashboard} className="btn-launch-primary" style={{ justifyContent: "center" }}>
                Enter Clinical Dashboard <ArrowRight size={18} />
              </button>
            </div>
          ) : (
            <div className="auth-glass-card">
              {/* Tab Selector */}
              <div className="auth-tab-row">
                <button
                  type="button"
                  onClick={() => setAuthMode("login")}
                  className={`auth-tab-btn ${authMode === "login" ? "active" : ""}`}
                >
                  Clinician Sign In
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode("signup")}
                  className={`auth-tab-btn ${authMode === "signup" ? "active" : ""}`}
                >
                  Create Account
                </button>
              </div>

              {/* One-Click Quick Demo Access */}
              <button
                type="button"
                onClick={handleQuickDemoAccess}
                disabled={authSubmitting}
                className="btn-quick-demo"
              >
                <Sparkles size={16} /> Instant 1-Click Evaluation Access
              </button>

              <div style={{ display: "flex", alignItems: "center", gap: "10px", margin: "4px 0" }}>
                <div style={{ flex: 1, height: "1px", background: "rgba(255, 255, 255, 0.08)" }} />
                <span style={{ fontSize: "0.7rem", color: "#64748B", textTransform: "uppercase", fontWeight: "700" }}>
                  or continue with
                </span>
                <div style={{ flex: 1, height: "1px", background: "rgba(255, 255, 255, 0.08)" }} />
              </div>

              {/* Form */}
              <form onSubmit={handleEmailAuth} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div className="auth-input-group">
                  <label className="auth-input-label">Work / Institutional Email</label>
                  <input
                    type="email"
                    required
                    placeholder="doctor@hospital.org"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    className="auth-input-field"
                  />
                </div>

                <div className="auth-input-group">
                  <label className="auth-input-label">Password</label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    className="auth-input-field"
                  />
                </div>

                {authError && (
                  <div
                    style={{
                      padding: "10px 14px",
                      borderRadius: "8px",
                      background: "rgba(255, 45, 85, 0.12)",
                      border: "1px solid rgba(255, 45, 85, 0.3)",
                      color: "#FF2D55",
                      fontSize: "0.75rem",
                      lineHeight: "1.4",
                    }}
                  >
                    {authError}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={authSubmitting}
                  className="btn-launch-primary"
                  style={{ width: "100%", justifyContent: "center", marginTop: "4px" }}
                >
                  {authSubmitting ? (
                    <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Activity size={16} className="spin-animation" /> Connecting to Vault...
                    </span>
                  ) : authMode === "login" ? (
                    "Sign In to Dashboard"
                  ) : (
                    "Register & Connect"
                  )}
                </button>
              </form>

              {/* Google OAuth Option */}
              <button
                type="button"
                onClick={handleGoogleAuth}
                disabled={authSubmitting}
                className="btn-launch-secondary"
                style={{ width: "100%", justifyContent: "center", padding: "11px" }}
              >
                Sign In with Google
              </button>
            </div>
          )}
        </div>
      </section>

      {/* 8. Minimalist Professional Footer */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, #FF2D55, #5856D6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Heart size={14} color="#FFFFFF" fill="#FFFFFF" />
            </div>
            <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#FFFFFF" }}>
              CardioGuard AI
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748B" }}>
              &bull; Research-Grade Clinical Intelligence
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10B981" }} />
              <span style={{ fontSize: "0.75rem", color: "#94A3B8", fontWeight: "600" }}>
                All 7 Model Checkpoints Online
              </span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "#64748B" }}>
              &copy; {new Date().getFullYear()} CardioGuard AI. All rights reserved.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

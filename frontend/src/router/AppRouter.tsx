import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import App from "../App";
import ErrorBoundary from "../components/ErrorBoundary";

// Lazy-load all page views
const Dashboard = lazy(() => import("../pages/Dashboard"));
const Trends = lazy(() => import("../pages/Trends"));
const Reports = lazy(() => import("../pages/Reports"));
const Notifications = lazy(() => import("../pages/Notifications"));
const Connections = lazy(() => import("../pages/Connections"));
const Settings = lazy(() => import("../pages/Settings"));
const Profile = lazy(() => import("../pages/Profile"));
const Coach = lazy(() => import("../pages/Coach"));
const Doctor = lazy(() => import("../pages/Doctor"));
const Devices = lazy(() => import("../pages/Devices"));
const SyncCenter = lazy(() => import("../pages/SyncCenter"));
const Privacy = lazy(() => import("../pages/Privacy"));
const Explainability = lazy(() => import("../pages/Explainability"));
const ModelRegistry = lazy(() => import("../pages/ModelRegistry"));
const DatasetManager = lazy(() => import("../pages/DatasetManager"));
const SystemMonitoring = lazy(() => import("../pages/SystemMonitoring"));
const Research = lazy(() => import("../pages/Research"));
const NotFound = lazy(() => import("../pages/NotFound"));

const LoadingFallback: React.FC = () => (
  <div style={{ display: "flex", flex: 1, justifyContent: "center", alignItems: "center", minHeight: "50vh" }}>
    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loading page...</div>
  </div>
);

export const AppRouter: React.FC = () => {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Main Layout Wrap Route */}
          <Route element={<App />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/connections" element={<Connections />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/coach" element={<Coach />} />
            <Route path="/doctor" element={<Doctor />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/sync-center" element={<SyncCenter />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/explainability" element={<Explainability />} />
            <Route path="/model-registry" element={<ModelRegistry />} />
            <Route path="/dataset-manager" element={<DatasetManager />} />
            <Route path="/system-monitoring" element={<SystemMonitoring />} />
            <Route path="/research" element={<Research />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
};

export default AppRouter;

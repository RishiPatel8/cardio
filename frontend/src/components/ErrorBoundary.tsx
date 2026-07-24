import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "40px", display: "flex", justifyContent: "center", alignItems: "center", minHeight: "50vh" }}>
          <div className="glass-panel" style={{ maxWidth: "500px", padding: "32px", textAlign: "center" }}>
            <h2 style={{ color: "var(--color-risk)", marginBottom: "12px", fontSize: "1.2rem" }}>Something went wrong.</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "20px" }}>
              The application encountered an error while loading this view.
            </p>
            <pre style={{ backgroundColor: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "8px", fontSize: "0.75rem", overflowX: "auto", textAlign: "left", color: "#FF3B30", border: "1px solid var(--border-glass)" }}>
              {this.state.error?.message || "Unknown error"}
            </pre>
            <button 
              onClick={() => window.location.reload()} 
              className="btn-primary" 
              style={{ marginTop: "20px", display: "inline-flex", margin: "0 auto" }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

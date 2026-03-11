import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("渲染错误:", error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <div style={{ padding: 24, fontFamily: "sans-serif" }}>
          <h2>页面加载出错</h2>
          <pre style={{ background: "#f5f5f5", padding: 16, overflow: "auto" }}>
            {this.state.error.message}
          </pre>
          <p style={{ color: "#666" }}>
            请确保后端已启动（uvicorn app.main:app --port 8000），并刷新页面。
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

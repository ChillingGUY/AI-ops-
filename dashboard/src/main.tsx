import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import App from "./App";
import { ErrorBoundary } from "./ErrorBoundary";

import "antd/dist/reset.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: "#1677ff" } }}>
        <App />
      </ConfigProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);


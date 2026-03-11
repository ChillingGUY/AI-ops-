import { useEffect, useMemo, useRef, useState } from "react";
import { Badge, Layout, Menu, Typography, notification } from "antd";
import type { MenuProps } from "antd";
import OverviewPage from "./pages/OverviewPage";
import AlertsPage from "./pages/AlertsPage";
import ServersPage from "./pages/ServersPage";
import RepairsPage from "./pages/RepairsPage";
import SimulationPage from "./pages/SimulationPage";
import SettingsPage from "./pages/SettingsPage";
import { fetchRecentAlerts } from "./api";

const { Header, Sider, Content } = Layout;

type PageKey = "overview" | "alerts" | "servers" | "repairs" | "simulation" | "settings";

function severityToBadgeStatus(sev?: string): "error" | "warning" | "default" | "processing" | "success" {
  const s = (sev || "").toLowerCase();
  if (s === "critical" || s === "fatal") return "error";
  if (s === "warning" || s === "warn") return "warning";
  return "processing";
}

export default function App() {
  const [page, setPage] = useState<PageKey>("overview");
  const [unread, setUnread] = useState<number>(0);
  const seenAlertIds = useRef<Set<number>>(new Set());

  const items: MenuProps["items"] = useMemo(
    () => [
      { key: "overview", label: "总览（整体监控）" },
      { key: "servers", label: "服务器" },
      { key: "alerts", label: "告警事件" },
      { key: "repairs", label: "自动化处置" },
      { key: "simulation", label: "仿真测试" },
      { key: "settings", label: "LLM 配置" },
    ],
    [],
  );

  useEffect(() => {
    let alive = true;

    async function poll() {
      try {
        const events = await fetchRecentAlerts(20);
        if (!alive) return;

        const newOnes = events.filter((e) => !seenAlertIds.current.has(e.id));
        if (newOnes.length > 0) {
          setUnread((x) => x + newOnes.length);
        }

        for (const e of newOnes.slice(0, 3)) {
          notification.open({
            message: `告警：${e.summary}`,
            description: e.details || `严重程度=${e.severity} 服务器ID=${e.server_id}`,
            placement: "topRight",
            duration: 6,
          });
        }
        newOnes.forEach((e) => seenAlertIds.current.add(e.id));
      } catch {
        // demo：忽略轮询错误
      }
    }

    poll();
    const timer = window.setInterval(poll, 5000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={240} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <div style={{ padding: 16 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            AIOps 智能运维平台
          </Typography.Title>
          <Typography.Text type="secondary">智能运维仪表盘</Typography.Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[page]}
          items={items}
          onClick={(e) => setPage(e.key as PageKey)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "white",
            borderBottom: "1px solid #f0f0f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            paddingInline: 16,
          }}
        >
          <Typography.Text strong style={{ fontSize: 16 }}>
            {page === "overview" ? "总览" : page === "servers" ? "服务器" : page === "alerts" ? "告警事件" : page === "repairs" ? "自动化处置" : page === "simulation" ? "仿真测试" : "LLM 配置"}
          </Typography.Text>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Badge count={unread} overflowCount={99} title="新告警数">
              <Typography.Text>告警气泡</Typography.Text>
            </Badge>
            <Badge status={severityToBadgeStatus("warning")} text="轮询 5s" />
          </div>
        </Header>
        <Content style={{ padding: 16 }}>
          {page === "overview" && <OverviewPage />}
          {page === "servers" && <ServersPage />}
          {page === "alerts" && <AlertsPage onViewedAll={() => setUnread(0)} />}
          {page === "repairs" && <RepairsPage />}
          {page === "simulation" && <SimulationPage />}
          {page === "settings" && <SettingsPage />}
        </Content>
      </Layout>
    </Layout>
  );
}


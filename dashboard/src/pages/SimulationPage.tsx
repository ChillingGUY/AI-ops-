import { useEffect, useState } from "react";
import { Button, Card, Space, Table, Tag, Typography } from "antd";
import {
  fetchSimulationStatus,
  fetchOptimizationLogs,
  startSimulation,
  stopSimulation,
} from "../api";

function fmtMetrics(m: Record<string, number> | undefined): string {
  if (!m || typeof m !== "object") return "-";
  const parts = ["cpu_usage", "mem_usage", "disk_usage"]
    .filter((k) => k in m)
    .map((k) => `${k.replace("_usage", "")}=${Math.round((m[k] ?? 0) * 100)}%`);
  return parts.join(" ") || "-";
}

export default function SimulationPage() {
  const [status, setStatus] = useState<{ running: boolean; cycle: number; last_events: Array<Record<string, unknown>> } | null>(null);
  const [optimizationLogs, setOptimizationLogs] = useState<Awaited<ReturnType<typeof fetchOptimizationLogs>>>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    try {
      const [statusData, logsData] = await Promise.all([
        fetchSimulationStatus(),
        fetchOptimizationLogs(undefined, 30),
      ]);
      setStatus(statusData);
      setOptimizationLogs(logsData);
    } catch {
      setStatus({ running: false, cycle: 0, last_events: [] });
      setOptimizationLogs([]);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, []);

  async function handleStart() {
    setLoading(true);
    try {
      await startSimulation(5);
      await load();
    } finally {
      setLoading(false);
    }
  }

  async function handleStop() {
    setLoading(true);
    try {
      await stopSimulation();
      await load();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Card title="仿真测试">
        <Typography.Paragraph>
          模拟真实环境：多台服务器 7x24 持续上报指标，告警由 AI 自动分类并执行处置（存储→删日志+备份，CPU→终止非业务进程），无需人工干预。可配置 LLM 接入大模型增强分析。
        </Typography.Paragraph>
        <Typography.Paragraph type="secondary">
          <strong>优化保护：</strong>在「服务器」页面对某台主机执行 AI 优化后，该主机 30 分钟内不会被仿真测试，以保持优化效果；总览可实时查看指标变化。
        </Typography.Paragraph>
        <Space>
          <Button
            type="primary"
            onClick={handleStart}
            loading={loading}
            disabled={status?.running}
          >
            启动仿真
          </Button>
          <Button
            danger
            onClick={handleStop}
            loading={loading}
            disabled={!status?.running}
          >
            停止仿真
          </Button>
        </Space>
        <div style={{ marginTop: 16 }}>
          <Tag color={status?.running ? "green" : "default"}>
            {status?.running ? "运行中" : "已停止"}
          </Tag>
          <Typography.Text type="secondary"> 周期数：{status?.cycle ?? 0}</Typography.Text>
        </div>
      </Card>

      <Card title="仿真事件流（实时）">
        <Typography.Paragraph type="secondary">
          下方表格每 2 秒刷新，展示最近仿真事件。告警触发后由 AI 自动处置并写入「自动化处置」记录。
        </Typography.Paragraph>
        <Table
          rowKey={(_, i) => String(i)}
          pagination={false}
          size="small"
          dataSource={status?.last_events ?? []}
          columns={[
            { title: "时间", dataIndex: "ts", width: 200, ellipsis: true },
            { title: "服务器", dataIndex: "server", width: 100 },
            { title: "场景", dataIndex: "scenario", width: 120, render: (v: string) => v ?? "-" },
            {
              title: "告警",
              dataIndex: "alerts",
              width: 140,
              render: (v: number[], r: Record<string, unknown>) =>
                r?.skipped ? (
                  <Tag color="blue">已优化，跳过</Tag>
                ) : v?.length ? (
                  <Tag color="red">{v.length} 条已自动处置</Tag>
                ) : (
                  "-"
                ),
            },
          ]}
        />
      </Card>

      <Card title="优化执行日志">
        <Typography.Paragraph type="secondary">
          服务器优化执行记录，含优化前后指标对比。优化后的主机在仿真中会被跳过以保持效果。
        </Typography.Paragraph>
        <Table
          rowKey={(r) => String(r.id)}
          pagination={{ pageSize: 5 }}
          size="small"
          dataSource={optimizationLogs}
          columns={[
            { title: "时间", dataIndex: "ts", width: 180, ellipsis: true },
            { title: "主机", dataIndex: "hostname", width: 90 },
            {
              title: "优化前",
              dataIndex: "metrics_before",
              width: 140,
              render: fmtMetrics,
            },
            {
              title: "优化后",
              dataIndex: "metrics_after",
              width: 140,
              render: fmtMetrics,
            },
            { title: "动作数", dataIndex: "actions_count", width: 70 },
            { title: "摘要", dataIndex: "summary", ellipsis: true },
          ]}
        />
      </Card>

      <Card title="验证说明">
        <Typography.Paragraph>
          <strong>全自动流程：</strong>仿真启动后，指标上报→触发告警→AI 分类（存储/CPU/内存等）→自动执行 Runbook→写入处置记录。
        </Typography.Paragraph>
        <Typography.Paragraph>
          <strong>验证步骤：</strong>启动仿真后，在「总览」「告警事件」「自动化处置」页面可看到实时数据更新。无需在终端运行脚本。
        </Typography.Paragraph>
        <Typography.Paragraph>
          <strong>优化流程：</strong>在「服务器」页面选择某主机→点击「AI 优化建议」→确认「执行优化」。优化后该主机 30 分钟内不被仿真测试，优化效果在总览可见；上方「优化执行日志」展示前后指标对比。
        </Typography.Paragraph>
      </Card>
    </div>
  );
}

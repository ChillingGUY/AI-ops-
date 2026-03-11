import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Col, Row, Select, Statistic, Table, Typography } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import ReactECharts from "echarts-for-react";
import { fetchLatestMetrics, fetchServers, LatestMetricItem } from "../api";

function fmtPercent(v?: number): string {
  if (v === undefined || v === null || Number.isNaN(v)) return "-";
  return `${Math.round(v * 100)}%`;
}

export default function OverviewPage() {
  const [items, setItems] = useState<LatestMetricItem[]>([]);
  const [servers, setServers] = useState<{ id: number; hostname: string }[]>([]);
  const [filter, setFilter] = useState<string>("all"); // "all" | server_id
  const [refreshing, setRefreshing] = useState(false);

  const pollInterval = filter !== "all" ? 2000 : 5000;

  const load = useCallback(async () => {
    const [metricsData, serversData] = await Promise.all([
      fetchLatestMetrics(),
      fetchServers(),
    ]);
    setItems(metricsData);
    setServers(serversData.map((s) => ({ id: s.id, hostname: s.hostname })));
  }, []);

  useEffect(() => {
    let alive = true;
    load();
    const t = window.setInterval(() => {
      if (!alive) return;
      load();
    }, pollInterval);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [load, pollInterval]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await load();
    } finally {
      setRefreshing(false);
    }
  }

  const filteredItems = useMemo(() => {
    if (filter === "all") return items;
    const sid = parseInt(filter, 10);
    return items.filter((x) => x.server_id === sid);
  }, [items, filter]);

  const agg = useMemo(() => {
    const cpu = filteredItems
      .map((x) => x.metrics["cpu_usage"])
      .filter((x) => typeof x === "number") as number[];
    const mem = filteredItems
      .map((x) => x.metrics["mem_usage"])
      .filter((x) => typeof x === "number") as number[];
    const disk = filteredItems
      .map((x) => x.metrics["disk_usage"])
      .filter((x) => typeof x === "number") as number[];
    const avg = (a: number[]) =>
      a.length ? a.reduce((p, c) => p + c, 0) / a.length : undefined;
    return {
      cpuAvg: avg(cpu),
      memAvg: avg(mem),
      diskAvg: avg(disk),
      count: filteredItems.length,
    };
  }, [filteredItems]);

  const chartOption = useMemo(() => {
    const hostnames = filteredItems.map((x) => x.hostname);
    const cpu = filteredItems.map((x) => x.metrics["cpu_usage"] ?? 0);
    const mem = filteredItems.map((x) => x.metrics["mem_usage"] ?? 0);
    const disk = filteredItems.map((x) => x.metrics["disk_usage"] ?? 0);
    const isSingle = filteredItems.length <= 1;
    return {
      tooltip: { trigger: "axis" },
      legend: { data: ["CPU", "内存", "磁盘"] },
      grid: { left: 30, right: 10, top: 40, bottom: 20, containLabel: true },
      xAxis: {
        type: "category",
        data: isSingle ? ["CPU", "内存", "磁盘"] : hostnames,
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 1,
        axisLabel: { formatter: (v: number) => `${Math.round(v * 100)}%` },
      },
      series: isSingle
        ? [
            {
              name: "使用率",
              type: "bar",
              data: [cpu[0] ?? 0, mem[0] ?? 0, disk[0] ?? 0],
              itemStyle: {
                color: (params: { dataIndex: number }) =>
                  ["#5470c6", "#91cc75", "#fac858"][params.dataIndex],
              },
            },
          ]
        : [
            { name: "CPU", type: "bar", data: cpu },
            { name: "内存", type: "bar", data: mem },
            { name: "磁盘", type: "bar", data: disk },
          ],
    };
  }, [filteredItems]);

  const statTitle = filter === "all" ? "监控主机数" : "当前主机";
  const statLabel = filter === "all" ? "平均" : "使用率";
  const currentHostname =
    filter === "all"
      ? agg.count
      : filteredItems[0]?.hostname ?? servers.find((s) => String(s.id) === filter)?.hostname ?? "-";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Typography.Text strong>监控范围：</Typography.Text>
            <Select
              value={filter}
              onChange={setFilter}
              style={{ width: 220, marginLeft: 8 }}
              options={[
                { value: "all", label: "全局（全部主机）" },
                ...servers.map((s) => ({
                  value: String(s.id),
                  label: `${s.hostname} (ID: ${s.id})`,
                })),
              ]}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshing}
              style={{ marginLeft: 8 }}
            >
              立即刷新
            </Button>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title={statTitle} value={currentHostname} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title={`CPU ${statLabel}`} value={fmtPercent(agg.cpuAvg)} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title={`内存 ${statLabel}`} value={fmtPercent(agg.memAvg)} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title={`磁盘 ${statLabel}`} value={fmtPercent(agg.diskAvg)} />
          </Card>
        </Col>
      </Row>

      <Card title={filter === "all" ? "整体监控（最新资源概况）" : "单服务器监控"}>
        <ReactECharts option={chartOption} style={{ height: 320 }} />
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          数据来自 /metrics/latest
          {filter !== "all" ? "（单服务器每 2 秒刷新，优化后即可看到变化）" : "（每 5 秒更新）"}
        </Typography.Paragraph>
      </Card>

      <Card title={filter === "all" ? "主机最新指标（表格）" : "当前主机指标"}>
        <Table
          rowKey={(r) => `${r.server_id}`}
          pagination={{ pageSize: 10 }}
          dataSource={filteredItems}
          columns={[
            { title: "主机名", dataIndex: "hostname" },
            {
              title: "CPU",
              render: (_, r) => fmtPercent(r.metrics["cpu_usage"]),
            },
            {
              title: "内存",
              render: (_, r) => fmtPercent(r.metrics["mem_usage"]),
            },
            {
              title: "磁盘",
              render: (_, r) => fmtPercent(r.metrics["disk_usage"]),
            },
          ]}
        />
      </Card>
    </div>
  );
}


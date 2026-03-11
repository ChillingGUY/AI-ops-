import { useEffect, useState } from "react";
import { Button, Card, List, message, Modal, Space, Table, Tag, Typography } from "antd";
import { RobotOutlined } from "@ant-design/icons";
import { AlertEvent, fetchRecentAlerts, fetchAlertAnalysis } from "../api";

function sevColor(sev?: string): string {
  const s = (sev || "").toLowerCase();
  if (s === "critical" || s === "fatal") return "red";
  if (s === "warning" || s === "warn") return "orange";
  return "blue";
}

export default function AlertsPage({ onViewedAll }: { onViewedAll: () => void }) {
  const [items, setItems] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [analysisModal, setAnalysisModal] = useState<{
    visible: boolean;
    loading: boolean;
    data: { summary: string; probable_causes: string[]; suggestions: string[] } | null;
  }>({ visible: false, loading: false, data: null });

  async function showAnalysis(eventId: number) {
    setAnalysisModal({ visible: true, loading: true, data: null });
    try {
      const data = await fetchAlertAnalysis(eventId);
      setAnalysisModal({ visible: true, loading: false, data });
    } catch (e) {
      message.error("获取 AI 分析失败");
      setAnalysisModal({ visible: false, loading: false, data: null });
    }
  }

  function closeAnalysis() {
    setAnalysisModal({ visible: false, loading: false, data: null });
  }

  async function load() {
    setLoading(true);
    try {
      const data = await fetchRecentAlerts(100);
      setItems(data);
      onViewedAll();
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <Card
        title="告警事件"
        extra={
          <Button onClick={load} loading={loading}>
            重新刷新
          </Button>
        }
      >
        <Typography.Paragraph type="secondary">
          告警数据来自接口；右上角每 5 秒轮询，新告警以气泡通知弹窗提示。
        </Typography.Paragraph>
        <Table
          rowKey={(r) => `${r.id}`}
          loading={loading}
          pagination={{ pageSize: 10 }}
          dataSource={items}
          columns={[
            { title: "时间", dataIndex: "ts", width: 220 },
            { title: "事件ID", dataIndex: "id", width: 90 },
            { title: "服务器ID", dataIndex: "server_id", width: 90 },
            {
              title: "严重程度",
              dataIndex: "severity",
              width: 120,
              render: (v) => <Tag color={sevColor(v)}>{String(v)}</Tag>,
            },
            { title: "摘要", dataIndex: "summary" },
            { title: "细节", dataIndex: "details" },
            {
              title: "操作",
              width: 100,
              render: (_: unknown, r: AlertEvent) => (
                <Button
                  type="link"
                  size="small"
                  icon={<RobotOutlined />}
                  onClick={() => showAnalysis(r.id)}
                >
                  AI 分析
                </Button>
              ),
            },
          ]}
        />
      </Card>
      <Modal
        title="告警 AI 诊断"
        open={analysisModal.visible}
        onCancel={closeAnalysis}
        footer={<Button onClick={closeAnalysis}>关闭</Button>}
        width={560}
      >
        {analysisModal.loading ? (
          <p>正在分析…</p>
        ) : analysisModal.data ? (
          <Space direction="vertical" style={{ width: "100%" }}>
            <p>{analysisModal.data.summary}</p>
            {analysisModal.data.probable_causes.length > 0 && (
              <div>
                <strong>可能原因：</strong>
                <List
                  size="small"
                  dataSource={analysisModal.data.probable_causes}
                  renderItem={(item) => <List.Item>• {item}</List.Item>}
                />
              </div>
            )}
            {analysisModal.data.suggestions.length > 0 && (
              <div>
                <strong>处置建议：</strong>
                <List
                  size="small"
                  dataSource={analysisModal.data.suggestions}
                  renderItem={(item) => (
                    <List.Item>
                      <RobotOutlined style={{ color: "#52c41a", marginRight: 8 }} />
                      {item}
                    </List.Item>
                  )}
                />
              </div>
            )}
          </Space>
        ) : null}
      </Modal>
    </>
  );
}


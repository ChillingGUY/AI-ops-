import { useEffect, useState } from "react";
import { Button, Card, List, message, Modal, Progress, Space, Table } from "antd";
import { AuditOutlined } from "@ant-design/icons";
import {
  fetchRepairs,
  fetchRepairEvaluation,
  fetchEventRepairsEvaluation,
  RepairItem,
} from "../api";

const statusText: Record<string, string> = {
  queued: "排队中",
  running: "执行中",
  succeeded: "成功",
  failed: "失败",
};

export default function RepairsPage() {
  const [items, setItems] = useState<RepairItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [evalModal, setEvalModal] = useState<{
    visible: boolean;
    loading: boolean;
    data: { score?: number; evaluation: string; improvements: string[] } | null;
  }>({ visible: false, loading: false, data: null });

  async function load() {
    setLoading(true);
    try {
      const data = await fetchRepairs(100);
      setItems(data);
    } finally {
      setLoading(false);
    }
  }

  async function showRepairEvaluation(repairId: number) {
    setEvalModal({ visible: true, loading: true, data: null });
    try {
      const data = await fetchRepairEvaluation(repairId);
      setEvalModal({ visible: true, loading: false, data });
    } catch (e) {
      message.error("获取效果评估失败");
      setEvalModal({ visible: false, loading: false, data: null });
    }
  }

  async function showEventEvaluation(eventId: number) {
    setEvalModal({ visible: true, loading: true, data: null });
    try {
      const data = await fetchEventRepairsEvaluation(eventId);
      setEvalModal({ visible: true, loading: false, data });
    } catch (e) {
      message.error("获取效果评估失败");
      setEvalModal({ visible: false, loading: false, data: null });
    }
  }

  function closeEval() {
    setEvalModal({ visible: false, loading: false, data: null });
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <Card
        title="自动化处置记录"
        extra={
          <Button onClick={load} loading={loading}>
            重新刷新
          </Button>
        }
      >
        <Table
          rowKey={(r) => `${r.id}`}
          loading={loading}
          pagination={{ pageSize: 10 }}
          dataSource={items}
          columns={[
            { title: "ID", dataIndex: "id", width: 70 },
            { title: "告警事件ID", dataIndex: "alert_event_id", width: 100 },
            { title: "执行时间", dataIndex: "ts", width: 200 },
            { title: "动作类型", dataIndex: "action_type", width: 100 },
            { title: "目标", dataIndex: "target", width: 180 },
            {
              title: "状态",
              dataIndex: "status",
              width: 90,
              render: (v: string) => statusText[v] ?? v,
            },
            { title: "输出", dataIndex: "output" },
            {
              title: "操作",
              width: 180,
              render: (_: unknown, r: RepairItem) => (
                <Space>
                  <Button
                    type="link"
                    size="small"
                    icon={<AuditOutlined />}
                    onClick={() => showRepairEvaluation(r.id)}
                  >
                    评估本次
                  </Button>
                  <Button
                    type="link"
                    size="small"
                    onClick={() => showEventEvaluation(r.alert_event_id)}
                  >
                    评估本告警
                  </Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>
      <Modal
        title="自动化运维效果评估"
        open={evalModal.visible}
        onCancel={closeEval}
        footer={<Button onClick={closeEval}>关闭</Button>}
        width={560}
      >
        {evalModal.loading ? (
          <p>正在评估…</p>
        ) : evalModal.data ? (
          <Space direction="vertical" style={{ width: "100%" }}>
            {evalModal.data.score != null && (
              <div>
                <strong>评分：</strong>
                <Progress percent={evalModal.data.score} status="active" style={{ maxWidth: 200 }} />
              </div>
            )}
            <p>{evalModal.data.evaluation}</p>
            {evalModal.data.improvements.length > 0 && (
              <div>
                <strong>改进建议：</strong>
                <List
                  size="small"
                  dataSource={evalModal.data.improvements}
                  renderItem={(item) => <List.Item>• {item}</List.Item>}
                />
              </div>
            )}
          </Space>
        ) : null}
      </Modal>
    </>
  );
}

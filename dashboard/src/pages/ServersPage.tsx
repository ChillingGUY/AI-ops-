import { useEffect, useState } from "react";
import { Button, Card, List, message, Modal, Space, Table, Tag } from "antd";
import { BulbOutlined, ThunderboltOutlined } from "@ant-design/icons";
import {
  fetchServers,
  fetchServerSuggestions,
  executeServerOptimization,
  ServerItem,
} from "../api";

export default function ServersPage() {
  const [items, setItems] = useState<ServerItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [suggestionsModal, setSuggestionsModal] = useState<{
    visible: boolean;
    loading: boolean;
    serverId: number | null;
    data: { summary: string; optimizations: string[]; risks?: string[] } | null;
  }>({ visible: false, loading: false, serverId: null, data: null });

  async function load() {
    setLoading(true);
    try {
      const data = await fetchServers();
      setItems(data);
    } finally {
      setLoading(false);
    }
  }

  async function showSuggestions(serverId: number) {
    setSuggestionsModal((m) => ({ ...m, visible: true, loading: true, serverId, data: null }));
    try {
      const data = await fetchServerSuggestions(serverId);
      setSuggestionsModal((m) => ({ ...m, loading: false, data }));
    } catch (e) {
      message.error("获取优化建议失败");
      setSuggestionsModal((m) => ({ ...m, visible: false, loading: false, serverId: null }));
    }
  }

  function closeSuggestions() {
    setSuggestionsModal({ visible: false, loading: false, serverId: null, data: null });
  }

  function handleExecuteOptimize() {
    const sid = suggestionsModal.serverId;
    if (!sid) return;
    Modal.confirm({
      title: "确认执行优化？",
      content:
        "平台将根据当前指标执行优化动作（如清理日志、限流等）。Demo 版为模拟执行，生产环境需对接真实运维接口。",
      okText: "执行优化",
      cancelText: "取消",
      onOk: async () => {
        setOptimizing(true);
        try {
          const res = await executeServerOptimization(sid);
          message.success(`已执行 ${res.executed} 个优化动作。在总览选择该服务器可实时查看优化后指标变化`);
          closeSuggestions();
          load();
        } catch (e) {
          message.error("执行优化失败");
        } finally {
          setOptimizing(false);
        }
      },
    });
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <Card
        title="服务器（资产/心跳）"
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
            { title: "ID", dataIndex: "id", width: 90 },
            { title: "主机名", dataIndex: "hostname" },
            { title: "操作系统", dataIndex: "os", width: 120 },
            {
              title: "标签",
              dataIndex: "tags",
              render: (v: Record<string, unknown>) =>
                Object.entries(v || {}).map(([k, val]) => (
                  <Tag key={k}>
                    {k}={String(val)}
                  </Tag>
                )),
            },
            { title: "最后上线", dataIndex: "last_seen_at", width: 220 },
            {
              title: "操作",
              width: 120,
              render: (_: unknown, r: ServerItem) => (
                <Button
                  type="link"
                  size="small"
                  icon={<BulbOutlined />}
                  onClick={() => showSuggestions(r.id)}
                >
                  AI 优化建议
                </Button>
              ),
            },
          ]}
        />
      </Card>
      <Modal
        title="服务器 AI 优化建议"
        open={suggestionsModal.visible}
        onCancel={closeSuggestions}
        footer={
          <Space>
            <Button onClick={closeSuggestions}>关闭</Button>
            {suggestionsModal.data && suggestionsModal.serverId != null && (
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                loading={optimizing}
                onClick={handleExecuteOptimize}
              >
                执行优化
              </Button>
            )}
          </Space>
        }
        width={560}
      >
        {suggestionsModal.loading ? (
          <p>正在生成优化建议…</p>
        ) : suggestionsModal.data ? (
          <Space direction="vertical" style={{ width: "100%" }}>
            <p>{suggestionsModal.data.summary}</p>
            <div>
              <strong>优化建议：</strong>
              <List
                size="small"
                dataSource={suggestionsModal.data.optimizations}
                renderItem={(item) => (
                  <List.Item>
                    <BulbOutlined style={{ color: "#1890ff", marginRight: 8 }} />
                    {item}
                  </List.Item>
                )}
              />
            </div>
            {suggestionsModal.data.risks && suggestionsModal.data.risks.length > 0 && (
              <div>
                <strong>潜在风险：</strong>
                <List
                  size="small"
                  dataSource={suggestionsModal.data.risks}
                  renderItem={(item) => (
                    <List.Item style={{ color: "#d46b08" }}>• {item}</List.Item>
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


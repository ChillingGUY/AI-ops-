import { useEffect, useState } from "react";
import { Button, Card, Form, Input, message, Select, Space, Typography } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { fetchLLMConfig, saveLLMConfig, LLMConfig } from "../api";

export default function SettingsPage() {
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  async function load() {
    setLoading(true);
    try {
      const data = await fetchLLMConfig();
      setConfig(data);
      form.setFieldsValue({
        provider: data.provider,
        api_base: data.api_base || "",
        api_key: "",
        model: data.model,
      });
    } catch (e) {
      message.error("加载配置失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onFinish(values: {
    provider: string;
    api_base?: string;
    api_key?: string;
    model?: string;
  }) {
    setSaving(true);
    try {
      await saveLLMConfig({
        provider: values.provider,
        api_base: values.api_base || undefined,
        api_key: values.api_key || undefined,
        model: values.model || undefined,
      });
      message.success("LLM 配置已保存");
      form.setFieldsValue({ api_key: "" });
      load();
    } catch (e) {
      message.error("保存失败");
    } finally {
      setSaving(false);
    }
  }

  function onProviderChange(provider: string) {
    const preset = config?.presets?.[provider];
    if (preset) {
      form.setFieldsValue({
        api_base: preset.api_base,
        model: preset.model,
      });
    } else if (provider === "none") {
      form.setFieldsValue({ api_base: "", model: "gpt-3.5-turbo" });
    }
  }

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          LLM 配置
        </Space>
      }
      loading={loading}
    >
      <Typography.Paragraph type="secondary">
        选择大模型供应商（千问 / 智谱 / DeepSeek / OpenAI），用于告警诊断、服务器优化、自动化评估。未配置时使用内置规则兜底。
      </Typography.Paragraph>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        style={{ maxWidth: 480 }}
        initialValues={{ provider: "none" }}
      >
        <Form.Item
          name="provider"
          label="大模型供应商"
          rules={[{ required: true }]}
        >
          <Select
            placeholder="请选择"
            onChange={onProviderChange}
            options={[
              { value: "none", label: "不使用（内置规则兜底）" },
              { value: "openai", label: "OpenAI" },
              { value: "qwen", label: "通义千问（阿里云）" },
              { value: "zhipu", label: "智谱 GLM" },
              { value: "deepseek", label: "DeepSeek" },
            ]}
          />
        </Form.Item>
        <Form.Item name="api_base" label="API 地址">
          <Input placeholder="留空则使用预设默认地址" />
        </Form.Item>
        <Form.Item name="api_key" label="API Key">
          <Input.Password placeholder="留空则不修改原有 Key" />
        </Form.Item>
        <Form.Item name="model" label="模型名称">
          <Input placeholder="如 gpt-3.5-turbo、qwen-turbo" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>
            保存配置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

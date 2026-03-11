import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export interface LatestMetricItem {
  server_id: number;
  hostname: string;
  metrics: Record<string, number>;
}

export interface AlertEvent {
  id: number;
  rule_id: number;
  server_id: number;
  ts: string;
  status: string;
  severity: string;
  summary: string;
  details?: string | null;
  context: Record<string, unknown>;
}

export interface ServerItem {
  id: number;
  hostname: string;
  os?: string | null;
  tags: Record<string, unknown>;
  last_seen_at?: string | null;
}

export async function fetchLatestMetrics(): Promise<LatestMetricItem[]> {
  const res = await api.get<{ items: LatestMetricItem[] }>("/metrics/latest");
  return res.data.items;
}

export async function fetchRecentAlerts(limit = 50): Promise<AlertEvent[]> {
  const res = await api.get<AlertEvent[]>(`/alerts/events?limit=${limit}`);
  return res.data;
}

/** 告警 AI 分析结果 */
export interface AlertAnalysis {
  event_id: number;
  anomaly: string;
  summary: string;
  probable_causes: string[];
  suggestions: string[];
  source: "llm" | "rule";
}

export async function fetchAlertAnalysis(eventId: number): Promise<AlertAnalysis> {
  const res = await api.get<AlertAnalysis>(`/alerts/events/${eventId}/analysis`);
  return res.data;
}

export async function fetchServers(): Promise<ServerItem[]> {
  const res = await api.get<ServerItem[]>("/servers");
  return res.data;
}

export interface RepairItem {
  id: number;
  alert_event_id: number;
  ts: string;
  action_type: string;
  target: string;
  status: string;
  output?: string | null;
}

export async function fetchRepairs(limit = 50): Promise<RepairItem[]> {
  const res = await api.get<RepairItem[]>(`/repairs?limit=${limit}`);
  return res.data;
}

export interface SimulationStatus {
  running: boolean;
  cycle: number;
  last_events: Array<{
    ts: string;
    server: string;
    scenario: string;
    alerts: number[];
    auto_repaired: number;
  }>;
}

export async function fetchSimulationStatus(): Promise<SimulationStatus> {
  const res = await api.get<SimulationStatus>("/simulation/status");
  return res.data;
}

export async function startSimulation(interval = 5): Promise<{ started: boolean; message: string }> {
  const res = await api.post<{ started: boolean; message: string }>(`/simulation/start?interval=${interval}`);
  return res.data;
}

export async function stopSimulation(): Promise<{ stopped: boolean; message: string }> {
  const res = await api.post<{ stopped: boolean; message: string }>("/simulation/stop");
  return res.data;
}

/** 服务器优化建议（AI 生成） */
export interface OptimizationSuggestions {
  source: "llm" | "rule";
  hostname: string;
  summary: string;
  optimizations: string[];
  risks?: string[];
}

export async function fetchServerSuggestions(serverId: number): Promise<OptimizationSuggestions> {
  const res = await api.get<OptimizationSuggestions>(`/servers/${serverId}/suggestions`);
  return res.data;
}

/** 自动化处置效果评估 */
export interface AutomationEvaluation {
  source: "llm" | "rule";
  score?: number;
  evaluation: string;
  improvements: string[];
  repair_id?: number;
  event_id?: number;
  actions_count?: number;
}

export async function fetchRepairEvaluation(repairId: number): Promise<AutomationEvaluation> {
  const res = await api.get<AutomationEvaluation>(`/repairs/${repairId}/evaluation`);
  return res.data;
}

export async function fetchEventRepairsEvaluation(eventId: number): Promise<AutomationEvaluation> {
  const res = await api.get<AutomationEvaluation>(`/repairs/events/${eventId}/evaluation`);
  return res.data;
}

/** LLM 配置 */
export interface LLMConfig {
  provider: string;
  api_base: string | null;
  api_key: string | null;
  model: string;
  presets: Record<string, { label: string; api_base: string; model: string }>;
}

export interface LLMConfigIn {
  provider: string;
  api_base?: string | null;
  api_key?: string | null;
  model?: string | null;
}

export async function fetchLLMConfig(): Promise<LLMConfig> {
  const res = await api.get<LLMConfig>("/settings/llm");
  return res.data;
}

export async function saveLLMConfig(cfg: LLMConfigIn): Promise<{ ok: boolean; message: string }> {
  const res = await api.post<{ ok: boolean; message: string }>("/settings/llm", cfg);
  return res.data;
}

export async function executeServerOptimization(serverId: number): Promise<{
  server_id: number;
  hostname: string;
  executed: number;
  steps: Array<{ target: string; output: string }>;
}> {
  const res = await api.post(`/servers/${serverId}/optimize`);
  return res.data;
}

/** 优化执行日志 */
export interface OptimizationLogItem {
  id: number;
  server_id: number;
  hostname: string;
  ts: string;
  metrics_before: Record<string, number>;
  metrics_after: Record<string, number>;
  actions_count: number;
  summary: string;
}

export async function fetchOptimizationLogs(
  serverId?: number,
  limit = 50
): Promise<OptimizationLogItem[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (serverId != null) params.set("server_id", String(serverId));
  const res = await api.get<{ items: OptimizationLogItem[] }>(
    `/servers/optimization-logs?${params}`
  );
  return res.data.items;
}


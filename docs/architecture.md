# 系统架构与核心模块设计（MVP → 可扩展）

## 1. 整体数据流

```
用户服务器（Linux/Docker）
        │
        │  Agent 采集（CPU/内存/磁盘/IO/日志）
        ▼
Metrics + Logs 上报（HTTP/JSON，后续可扩展 gRPC/Kafka）
        ▼
API Gateway（FastAPI）
        ▼
AIOps Backend（模块化服务层）
        ├─ Server Manager（资产与心跳）
        ├─ Metrics Collector（指标入库、聚合）
        ├─ Log Center（日志入库、索引/归档）
        ├─ Alert Engine（规则/去重/抑制/通知）
        ├─ AI Analyzer（异常分析、根因推测）
        ├─ Resource Optimizer（优化建议）
        ├─ Capacity Predictor（容量预测）
        └─ Auto Repair Engine（自动修复/Runbook）
        ▼
存储层（PostgreSQL/Redis/MinIO） + AI 推理层（LLM/RAG/LangChain）
        ▼
Dashboard（React/ECharts）
```

## 2. 核心模块（职责边界）

### 2.1 Server Manager
- **职责**：管理服务器资产（hostname/os/tags）、最后上线时间（last seen）、（可扩展）agent 版本/能力协商。
- **输入**：每次 ingest 内含 server metadata（当作心跳）。
- **输出**：资产列表、存活状态、分组（tags）。

### 2.2 Metrics Collector
- **职责**：接收时序指标并入库；（可扩展）下采样、聚合（1m/5m/1h）、保留策略（TTL）。
- **MVP**：直接写入 `metric_samples`。
- **扩展点**：
  - Prometheus remote_write 相容層
  - 高频指标进 TimescaleDB/ClickHouse
  - Redis/Kafka 作为缓冲队列避免尖峰打爆 DB

### 2.3 Log Center
- **职责**：接收结构化日志；（可扩展）解析、索引、归档到 MinIO（冷存）。
- **MVP**：写入 `log_events`（message + fields）。
- **扩展点**：
  - 日志全文索引（OpenSearch/ClickHouse）
  - 冷热分层：近 7 天 PostgreSQL，历史 MinIO（parquet/jsonl）

### 2.4 Alert Engine
- **职责**：规则告警、去重（同 rule+server）、抑制（maintenance window）、通知（Webhook/Email/IM）。
- **MVP**：指标阈值规则，判定即写 `alert_events`。
- **扩展点**：
  - 规则语言（PromQL-like / JSON DSL）
  - 去重 key：`(rule_id, server_id, labels_hash)`，带 `fingerprint`
  - 告警生命周期：firing → resolved（自动恢复）

### 2.5 AI Analyzer（LLM/RAG）
- **职责**：为告警事件/异常时间窗提供根因候选与处置建议。
- **MVP**：stub 返回固定建议。
- **扩展点**：
  - RAG：以 runbook、历史事件、拓扑（CMDB）做检索
  - LLM：输入告警 + 关联 logs/metrics 的摘要，输出 RCA 与 SOP
  - 评估：用历史事件回放做离线指标（命中率、建议采纳率）

### 2.6 Resource Optimizer
- **职责**：基于一段时间的资源使用趋势（P95/P99）给出配额/实例建议。
- **输出**：CPU/Memory requests/limits 建议、Pod 水平扩缩策略建议。
- **扩展点**：结合 Kubernetes API/云端 API 写回建议或自动调整。

### 2.7 Capacity Predictor
- **职责**：针对容量相关指标（磁盘/DB size/流量）做预测，输出到达阈值的 ETA。
- **MVP**：stub。
- **扩展点**：
  - Prophet/ARIMA/ETS 或深度模型
  - 用节假日/促销特征做外生变量

### 2.8 Auto Repair Engine
- **职责**：根据告警类型触发自动化（runbook、webhook、job），并记录执行结果。
- **MVP**：提供 `repair_actions` 表（queued/running/succeeded/failed）。
- **扩展点**：
  - 支持多目标：SSH、K8s Job、Webhook、Ansible
  - 风险管控：灰度、人工确认、回滚

## 3. MVP 数据模型（目前已落地）
- `servers`：资产与 last_seen
- `metric_samples`：时序指标（server_id + name + ts）
- `log_events`：结构化日志
- `alert_rules`：指标阈值告警规则
- `alert_events`：告警事件
- `repair_actions`：自动修复动作记录

## 4. Dashboard（前端建议）
- **视图**：
  - Overview：整体健康度（当前 firing 数、关键服务）
  - Servers：服务器列表 + 最近心跳
  - Metrics：CPU/Mem/Disk/IO 折线（ECharts）
  - Logs：时间窗搜索/过滤/关联告警
  - Alerts：规则管理、事件时间线、AI 分析结果
  - Capacity：容量趋势与预测 ETA
  - Repairs：自动修复记录与输出


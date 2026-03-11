# AI-ops-

本项目旨在构建一个**面向中国市场的 AIOps 智能运维平台**，实现：

- **7x24 自动化监控**：对服务器/应用进行持续指标与日志采集
- **智能告警与分类**：AI 自动识别告警类型（存储/CPU/内存/网络/应用错误）
- **自动化处置**：根据分类执行对应 Runbook，减少人工介入
- **可扩展架构**：预留 LLM 大模型、RAG、Kafka 等接入点

### 1.2 技术定位

- **Demo / MVP**：当前版本为演示与验证用，不直接用于生产
- **二次开发友好**：模块清晰、接口规范，便于按业务需求扩展
- **国产化适配**：界面与文档均为简体中文，可接入国产大模型

---

## 二、系统设计

### 2.1 整体架构

```
用户服务器（Linux/Docker）
        │
        │  Agent 采集（CPU/内存/磁盘/IO/日志）
        ▼
Metrics + Logs 上报（HTTP/JSON）
        ▼
API Gateway（FastAPI）
        ▼
AIOps Backend
        ├─ Server Manager    资产与心跳
        ├─ Metrics Collector 指标入库
        ├─ Log Center        日志入库
        ├─ Alert Engine      规则告警
        ├─ AI 告警分类       存储/CPU/内存等
        ├─ 自动化处置        按分类执行 Runbook
        └─ 仿真测试          后台模拟 7x24 验证
        ▼
存储层（PostgreSQL/Redis/MinIO）+ 可选 LLM
        ▼
Dashboard（React + ECharts）
```

### 2.2 核心流程

1. **数据采集**：Agent 定期上报 CPU/内存/磁盘等指标及日志
2. **规则告警**：指标超过阈值触发告警
3. **AI 分类**：根据告警内容判断类型（存储/CPU/内存等）
4. **自动处置**：执行预设 Runbook（如存储→删日志+备份，CPU→终止非业务进程）
5. **可视化**：Dashboard 展示总览、告警、处置记录

### 2.3 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Ant Design + ECharts |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 存储 | MinIO（日志归档） |
| 部署 | Docker Compose |

---

## 三、如何使用

### 3.1 快速启动（Docker）

```bash
cd d:\shizhan
docker compose up --build
```

- 后端 API：http://localhost:8000/docs  
- 前端仪表盘：http://localhost:3000  

### 3.2 本机开发

**后端：**
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd dashboard
npm install
npm run dev
```

### 3.3 仿真测试验证

1. 打开 http://localhost:3000  
2. 进入「仿真测试」页面  
3. 点击「启动仿真」  
4. 在「总览」「告警事件」「自动化处置」页面观察实时数据  

仿真在后台运行，无需终端脚本，告警自动由 AI 分类并处置。

### 3.4 其他文档

- `docs/新手测试文档.md`：API 手工测试步骤  
- `docs/E2E全模块测试指南.md`：端到端测试说明  
- `docs/agent-install.md`：Agent 安装与上报  

---

## 四、Git 仓库描述

### 4.1 项目简介（可用于 README / 仓库描述）

```
AIOps 智能运维平台 | 7x24 监控 · AI 告警分类 · 自动化处置

面向中国市场的智能运维 Demo，支持：
- 多服务器指标/日志集中采集
- 告警规则 + AI 自动分类（存储/CPU/内存/网络/应用错误）
- 按分类执行 Runbook（存储→删日志+备份，CPU→终止非业务进程）
- 前端仿真测试、实时仪表盘
- 预留 LLM 大模型接入

技术栈：FastAPI + React + SQLAlchemy + ECharts
```

### 4.2 仓库标签建议

`aiops` `智能运维` `监控` `告警` `自动化` `FastAPI` `React` `Python`

---

## 五、二次开发指南

### 5.1 目录结构

```
shizhan/
├── backend/           # 后端
│   ├── app/
│   │   ├── routers/   # API 路由
│   │   ├── services/  # 业务逻辑（告警分类、处置、仿真）
│   │   ├── models.py  # 数据模型
│   │   └── schemas.py # 请求/响应结构
│   └── tests/
├── dashboard/         # 前端
│   └── src/
│       ├── pages/     # 页面组件
│       └── api.ts     # API 封装
├── agent/             # 采集 Agent 示例
├── scripts/           # 模拟脚本
└── docs/              # 文档
```

### 5.2 常见扩展场景

| 需求 | 修改位置 | 说明 |
|------|----------|------|
| 新增 API | `backend/app/routers/` | 新建 router 并在 `main.py` 注册 |
| 接入 LLM | `backend/app/services/llm_client.py` | 实现 `call_llm_for_classify` 等 |
| 新增告警分类 | `backend/app/services/alert_classifier.py` | 增加规则或调用 LLM |
| 新增 Runbook | `backend/app/services/auto_repair.py` | 在 `RUNBOOKS` 中增加步骤 |
| 新增页面 | `dashboard/src/pages/` | 新建组件并在 `App.tsx` 加菜单 |
| 对接 Kafka | 新建 `backend/app/services/kafka_ingest.py` | 消费指标/日志后写入 DB |

### 5.3 配置与环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| DATABASE_URL | 数据库连接 | sqlite:///./aiops.db |
| REDIS_URL | Redis 连接 | redis://localhost:6379/0 |
| LLM_PROVIDER | 大模型供应商 | none |
| LLM_API_BASE | 大模型 API 地址 | - |
| LLM_API_KEY | 大模型 API Key | - |
| LLM_MODEL | 大模型名称 | gpt-3.5-turbo |

### 5.3.1 LLM 大模型配置说明

平台支持在界面上选择 **千问 / 智谱 / DeepSeek / OpenAI** 四种供应商。配置保存在 `backend/data/llm_config.json`，优先级高于环境变量。未配置 LLM 时，告警诊断、优化建议、自动化评估等会使用内置规则兜底。

**配置入口**：侧边栏 → **LLM 配置** → 选择供应商、填写 API Key、保存。

| 供应商 | API Base 默认值 | 模型示例 |
|--------|-----------------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-3.5-turbo |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |
| 智谱 GLM | https://open.bigmodel.cn/api/paas/v4 | glm-4-flash |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |

**环境变量（可选，作为默认/后备）：**

```bash
LLM_PROVIDER=openai    # openai | qwen | zhipu | deepseek | none
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-3.5-turbo
```

**使用场景：**
- **告警诊断**：点击告警事件的「AI 分析」，由 LLM 分析根因并给出处置建议
- **服务器优化**：在服务器列表点击「AI 优化建议」，基于指标与告警历史生成优化方案；用户可选择「执行优化」按钮，确认后由平台执行优化动作（Demo 版为模拟执行）
- **自动化评估**：在处置记录中点击「评估本次」或「评估本告警」，由 LLM 评估处置效果与改进建议

### 5.4 数据模型扩展

- 新增表：在 `backend/app/models.py` 定义，`init_db()` 会自动建表  
- 新增字段：修改对应 Model，本机开发时删除 `aiops.db` 重新启动即可（或使用迁移工具）

---

## 六、上线与业务对接

### 6.1 上线前准备

1. **数据库**：使用 PostgreSQL，配置 `DATABASE_URL`
2. **Redis**：用于缓存/限流（按需）
3. **对象存储**：MinIO 或 OSS，用于日志归档
4. **网络**：确保业务服务器可访问 API 地址（或通过内网 Agent）

### 6.2 业务对接方式

| 对接场景 | 方式 | 说明 |
|----------|------|------|
| 指标上报 | HTTP `POST /ingest/metrics` | Agent 或业务系统直接调用 |
| 日志上报 | HTTP `POST /ingest/logs` | 同上 |
| 告警通知 | 扩展 Alert Engine | 增加 Webhook/钉钉/企业微信/邮件 |
| 调用业务接口 | 扩展 Auto Repair | Runbook 中增加 HTTP 调用业务 API |
| 数据同步 | 扩展 API 或定时任务 | 从 CMDB/业务系统同步资产等信息 |

### 6.3 与现有监控体系对接

- **Prometheus**：可增加 Prometheus remote_write 兼容接口，将指标写入本平台  
- **日志系统**：可增加 Fluentd/Filebeat 输出插件，将日志转发到 `POST /ingest/logs`  
- **告警平台**：可通过 Webhook 接收本平台告警，或本平台接收外部告警做二次分析  

### 6.4 安全与权限

- **API 认证**：当前无认证，上线需增加 API Key / JWT / OAuth  
- **网络隔离**：建议 API 仅内网访问，Agent 与平台同网段  
- **敏感信息**：LLM API Key、数据库密码等使用环境变量或密钥管理服务  

### 6.5 运维建议

- 定期备份 PostgreSQL  
- 配置日志轮转与保留策略  
- 监控平台自身（CPU/内存/磁盘）  
- 参考 `docs/ops-runbook.md` 进行巡检与故障处理  

---

## 七、文档索引

| 文档 | 用途 |
|------|------|
| `README.md` | 快速开始 |
| `docs/新手运维文档.md` | 本文档，整体说明与二次开发 |
| `docs/新手测试文档.md` | API 手工测试 |
| `docs/E2E全模块测试指南.md` | 仿真与端到端测试 |
| `docs/architecture.md` | 架构与模块设计 |
| `docs/api.md` | API 规格 |
| `docs/agent-install.md` | Agent 安装 |
| `docs/ops-runbook.md` | 部署、巡检、故障处理 |




测试方法

## 一、启动服务

### 方式 A：Docker（推荐）

```bash
cd d:\shizhan
docker compose up --build
```

### 方式 B：本机运行

```powershell
cd d:\shizhan\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

启动成功后，默认地址为：`http://localhost:8000`。

---

## 二、访问 Swagger 文档

在浏览器中打开：

- **API 文档**：http://localhost:8000/docs  
- **健康检查**：http://localhost:8000/health

健康检查应返回：

```json
{"status": "正常", "message": "服务运行正常"}
```

---

## 三、测试步骤（按顺序）

### 步骤 1：健康检查

- **接口**：`GET /health`
- **操作**：在 Swagger 中展开「健康检查」→ 点击 `GET /health` → 点击「Try it out」→「Execute」
- **预期**：状态码 200，返回 `{"status": "正常", "message": "服务运行正常"}`

---

### 步骤 2：创建告警规则

- **接口**：`POST /alerts/rules`
- **操作**：展开「告警」→ 点击 `POST /alerts/rules` →「Try it out」
- **请求体示例**：

```json
{
  "name": "CPU 过高",
  "enabled": true,
  "metric_name": "cpu_usage",
  "comparator": ">",
  "threshold": 0.9,
  "for_seconds": 60,
  "severity": "critical",
  "labels": {}
}
```

- **字段说明**：
  - `name`：规则名称
  - `metric_name`：指标名，如 `cpu_usage`、`mem_usage`、`disk_usage`
  - `comparator`：比较符，`>` 表示大于
  - `threshold`：阈值，0.9 表示 90%
  - `severity`：严重程度，`critical` 或 `warning`
- **预期**：状态码 200，返回包含 `id` 的规则对象

---

### 步骤 3：上报监控指标

- **接口**：`POST /ingest/metrics`
- **操作**：展开「数据上报」→ 点击 `POST /ingest/metrics` →「Try it out」
- **请求体示例**：

```json
{
  "server": {
    "hostname": "demo-server-1",
    "os": "linux",
    "tags": { "env": "demo" }
  },
  "points": [
    {
      "ts": "2026-03-06T12:00:00Z",
      "name": "cpu_usage",
      "value": 0.95,
      "labels": {}
    },
    {
      "ts": "2026-03-06T12:00:00Z",
      "name": "mem_usage",
      "value": 0.7,
      "labels": {}
    }
  ]
}
```

- **说明**：`value` 为 0.95 表示 CPU 95%，会触发步骤 2 中「CPU > 90%」的规则。
- **预期**：状态码 200，返回 `server_id`、`ingested`、`alerts_fired`（可能包含新告警 ID）

---

### 步骤 4：查看告警事件

- **接口**：`GET /alerts/events`
- **操作**：展开「告警」→ 点击 `GET /alerts/events` →「Try it out」→「Execute」
- **预期**：状态码 200，返回告警事件数组，可看到步骤 3 触发的事件

---

### 步骤 5：查看服务器列表

- **接口**：`GET /servers`
- **操作**：展开「服务器」→ 点击 `GET /servers` →「Try it out」→「Execute」
- **预期**：状态码 200，返回服务器列表，包含 `demo-server-1`

---

### 步骤 6：上报日志

- **接口**：`POST /ingest/logs`
- **操作**：展开「数据上报」→ 点击 `POST /ingest/logs` →「Try it out」
- **请求体示例**：

```json
{
  "server": {
    "hostname": "demo-server-1",
    "os": "linux",
    "tags": {}
  },
  "events": [
    {
      "ts": "2026-03-06T12:00:00Z",
      "level": "ERROR",
      "message": "数据库连接超时",
      "source": "app",
      "fields": { "trace_id": "t-001" }
    }
  ]
}
```

- **预期**：状态码 200，返回 `server_id` 和 `ingested`

---

### 步骤 7：查看最新指标（可选）

- **接口**：`GET /metrics/latest`
- **操作**：展开「指标」→ 点击 `GET /metrics/latest` →「Try it out」→「Execute」
- **预期**：状态码 200，返回各服务器最新 CPU/内存/磁盘等指标

---

### 步骤 8：告警 AI 分析（可选）

- **接口**：`GET /alerts/events/{event_id}/analysis`
- **操作**：先通过步骤 4 获取一个告警事件 ID，再在 Swagger 中调用此接口，将 `event_id` 替换为实际 ID
- **预期**：返回根因分析摘要、可能原因与处置建议（Demo 为固定示例）

---

## 四、Schema 中文说明速查

| Schema       | 中文说明       | 主要字段说明                           |
|-------------|----------------|----------------------------------------|
| 服务器信息   | Agent 上报用   | hostname、os、tags                     |
| 服务器       | 已注册资产     | id、hostname、last_seen_at             |
| 指标点       | 单条监控数据   | ts、name（cpu_usage 等）、value        |
| 指标上报     | 批量上报       | server、points                         |
| 日志事件     | 单条日志       | ts、level、message、source             |
| 日志上报     | 批量日志       | server、events                         |
| 告警规则     | 阈值规则       | name、metric_name、comparator、threshold |
| 告警事件     | 已触发告警     | id、rule_id、severity、summary         |

---

## 五、常见问题

**Q：健康检查返回 500？**  
A：检查数据库连接。本机默认使用 SQLite，应自动创建 `backend/aiops.db`；若用 Docker，确认 PostgreSQL 已启动。

**Q：上报指标后没有告警？**  
A：确认已先创建告警规则，且指标的 `name`、`value` 满足规则条件（如 `cpu_usage > 0.9`）。

**Q：时间格式怎么写？**  
A：使用 ISO 8601 格式，例如：`2026-03-06T12:00:00Z` 或 `2026-03-06T12:00:00+08:00`。

---

## 六、下一步

- 访问 Dashboard：http://localhost:3000（需 Docker 或单独启动前端）
- 配置 Agent 自动上报：参考 `docs/agent-install.md`
- 了解架构设计：参考 `docs/architecture.md`

<<<<<<< HEAD
# AIOps 智能运维平台（Demo / MVP）

> 面向中国市场的智能运维平台，支持 7x24 监控、AI 告警分类、自动化处置，可接入大模型增强分析。

## Git 项目描述（创建仓库时可使用）

```
AIOps 智能运维平台 | 7x24 监控 · AI 告警分类 · 自动化处置

- 多服务器指标/日志集中采集
- 告警规则 + AI 自动分类（存储/CPU/内存/网络/应用错误）
- 按分类执行 Runbook（存储→删日志+备份，CPU→终止非业务进程）
- 前端仿真测试、实时仪表盘，预留 LLM 接入

技术栈：FastAPI + React + SQLAlchemy + ECharts
```

---

## 功能概览

本项目提供一个可落地的 AIOps 智能运维平台 Demo 骨架，覆盖：

- 7x24 监控（Metrics/Logs 上报）
- 日志集中管理
- 告警引擎（规则 + 阈值触发）
- AI 告警分类（存储/CPU/内存/网络/应用错误）
- 自动化处置（告警触发后自动执行 Runbook，无需人工）
- 仿真测试（前端一键启动后台模拟，验证整套流程）
- 运维仪表盘（React + ECharts，含气泡弹窗告警）
- 预留 LLM 大模型、RAG、容量预测等扩展点

## 方式一：Docker 一键启动（推荐，环境封装）

前置：已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

```bash
cd d:\shizhan
docker compose up --build
```

启动后：

- Backend API：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`
- Dashboard（前端）：`http://localhost:3000`

**说明**：Docker 模式使用 PostgreSQL + Redis + MinIO，数据持久化在 volumes 中。

---

## 方式二：本机开发（无需 Docker、无需 PostgreSQL）

本机默认使用 SQLite，无需安装或启动任何数据库。

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 数据文件：`backend/aiops.db`（SQLite）
- API：`http://localhost:8000/docs`

若需用 PostgreSQL，可设置环境变量：
`$env:DATABASE_URL = "postgresql+psycopg://aiops:aiops@localhost:5432/aiops"`

## 测试（Backend）

```bash
cd backend
pytest -q
```

## 文档

- `docs/新手运维文档.md`：**新手必读**，项目目的、设计、使用、二次开发、上线对接
- `docs/architecture.md`：核心模块与系统设计
- `docs/新手测试文档.md`：API 手工测试步骤
- `docs/E2E全模块测试指南.md`：仿真测试与端到端验证
- `docs/api.md`：上报/查询 API 规格
- `docs/agent-install.md`：Agent 安装与上报示例
- `docs/ops-runbook.md`：部署、巡检、告警、故障处理
=======
# AIOps 智能运维平台（Demo / MVP）

> 面向中国市场的智能运维平台，支持 7x24 监控、AI 告警分类、自动化处置，可接入大模型增强分析。

## Git 项目描述

```
AIOps 智能运维平台 | 7x24 监控 · AI 告警分类 · 自动化处置

- 多服务器指标/日志集中采集
- 告警规则 + AI 自动分类（存储/CPU/内存/网络/应用错误）
- 按分类执行 Runbook（存储→删日志+备份，CPU→终止非业务进程）
- 前端仿真测试、实时仪表盘，预留 LLM 接入

技术栈：FastAPI + React + SQLAlchemy + ECharts
```

---

## 功能概览

本项目提供一个可落地的 AIOps 智能运维平台 Demo 骨架，覆盖：

- 7x24 监控（Metrics/Logs 上报）
- 日志集中管理
- 告警引擎（规则 + 阈值触发）
- AI 告警分类（存储/CPU/内存/网络/应用错误）
- 自动化处置（告警触发后自动执行 Runbook，无需人工）
- 仿真测试（前端一键启动后台模拟，验证整套流程）
- 运维仪表盘（React + ECharts，含气泡弹窗告警）
- 预留 LLM 大模型、RAG、容量预测等扩展点

## 方式一：Docker 一键启动（推荐，环境封装）

前置：已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

```bash
cd d:\shizhan
docker compose up --build
```

启动后：

- Backend API：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`
- Dashboard（前端）：`http://localhost:3000`

**说明**：Docker 模式使用 PostgreSQL + Redis + MinIO，数据持久化在 volumes 中。

---

## 方式二：本机开发（无需 Docker、无需 PostgreSQL）

本机默认使用 SQLite，无需安装或启动任何数据库。

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 数据文件：`backend/aiops.db`（SQLite）
- API：`http://localhost:8000/docs`

若需用 PostgreSQL，可设置环境变量：
`$env:DATABASE_URL = "postgresql+psycopg://aiops:aiops@localhost:5432/aiops"`

## 测试（Backend）

```bash
cd backend
pytest -q
```

## 文档

- `docs/新手运维文档.md`：**新手必读**，项目目的、设计、使用、二次开发、上线对接
- `docs/architecture.md`：核心模块与系统设计
- `docs/新手测试文档.md`：API 手工测试步骤
- `docs/E2E全模块测试指南.md`：仿真测试与端到端验证
- `docs/api.md`：上报/查询 API 规格
- `docs/agent-install.md`：Agent 安装与上报示例
- `docs/ops-runbook.md`：部署、巡检、告警、故障处理

>>>>>>> 9e2f3a057719e6943ae77a6b144d265970918b8a

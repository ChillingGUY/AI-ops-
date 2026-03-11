# AIOps 智能运维平台 E2E 全模块测试指南

本指南用于完整测试所有模块：多服务器 7x24 监控、告警预报、AI 自动识别告警内容、分类处置（如存储问题→删除日志并备份，CPU 过载→终止非业务进程）。

---

## 一、模块概览

| 模块 | 功能 |
|------|------|
| 健康检查 | 服务状态 |
| 服务器管理 | 资产注册、心跳 |
| 指标采集 | CPU/内存/磁盘上报 |
| 日志中心 | 结构化日志上报 |
| 告警引擎 | 规则 + 阈值触发 |
| AI 告警分类 | 存储/CPU/内存/网络/应用错误 |
| 自动化处置 | 按分类执行 Runbook，**告警触发后自动执行，无需人工** |
| 仿真测试 | 后台模拟 7x24 上报，全自动验证整套流程 |
| 仪表盘 | 总览、告警、处置、仿真（前端可视化验证） |

---

## 二、启动服务

```powershell
cd D:\shizhan\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

或使用 Docker：`docker compose up --build`

---

## 三、手动测试流程

### 步骤 1：创建告警规则

在 `http://localhost:8000/docs` 中调用 `POST /alerts/rules`：

```json
{"name": "CPU 过高", "metric_name": "cpu_usage", "comparator": ">", "threshold": 0.9, "severity": "critical"}
{"name": "内存过高", "metric_name": "mem_usage", "comparator": ">", "threshold": 0.9, "severity": "critical"}
{"name": "磁盘过高", "metric_name": "disk_usage", "comparator": ">", "threshold": 0.85, "severity": "warning"}
```

### 步骤 2：模拟多台服务器上报

对多台服务器分别调用 `POST /ingest/metrics`，制造不同场景：

**场景 A - CPU 过载（触发 CPU 告警）**

```json
{
  "server": {"hostname": "web-srv-01", "os": "linux", "tags": {"env": "prod"}},
  "points": [
    {"ts": "2026-03-06T12:00:00Z", "name": "cpu_usage", "value": 0.95, "labels": {}},
    {"ts": "2026-03-06T12:00:00Z", "name": "mem_usage", "value": 0.5, "labels": {}},
    {"ts": "2026-03-06T12:00:00Z", "name": "disk_usage", "value": 0.6, "labels": {}}
  ]
}
```

**场景 B - 存储紧张（触发磁盘告警）**

```json
{
  "server": {"hostname": "db-srv-03", "os": "linux", "tags": {"env": "prod"}},
  "points": [
    {"ts": "2026-03-06T12:00:00Z", "name": "cpu_usage", "value": 0.3, "labels": {}},
    {"ts": "2026-03-06T12:00:00Z", "name": "mem_usage", "value": 0.5, "labels": {}},
    {"ts": "2026-03-06T12:00:00Z", "name": "disk_usage", "value": 0.93, "labels": {}}
  ]
}
```

**场景 C - 内存不足**

```json
{
  "server": {"hostname": "api-srv-02", "os": "linux", "tags": {}},
  "points": [
    {"ts": "2026-03-06T12:00:00Z", "name": "cpu_usage", "value": 0.4, "labels": {}},
    {"ts": "2026-03-06T12:00:00Z", "name": "mem_usage", "value": 0.92, "labels": {}},
    {"ts": "2026-03-06T12:00:00Z", "name": "disk_usage", "value": 0.6, "labels": {}}
  ]
}
```

### 步骤 3：查看告警并执行 AI 分类

1. 调用 `GET /alerts/events` 获取告警事件 ID（例如 `event_id=1`）
2. 调用 `GET /repairs/events/1/classify` 查看 AI 分类结果：
   - CPU 过载 → `{"category": "cpu", "label": "CPU 过载"}`
   - 磁盘过高 → `{"category": "disk", "label": "存储问题"}`
   - 内存过高 → `{"category": "memory", "label": "内存不足"}`

### 步骤 4：执行自动化处置

调用 `POST /repairs/events/1/execute`（将 `1` 替换为实际事件 ID）：

- **存储问题**：执行「删除过期日志释放空间」「备份关键数据并归档」
- **CPU 过载**：执行「终止非业务相关进程降低负载」「限流后台任务」
- **内存不足**：执行「检查内存泄漏」「建议扩容或重启服务」

Demo 版为**模拟执行**，动作会写入 `repair_actions` 表，不执行真实系统命令。

### 步骤 5：查看处置记录

调用 `GET /repairs` 查看所有处置记录。

---

## 四、前端仿真测试（推荐，无需终端）

在 AIOps 智能运维平台前端完成全流程验证，仿真在后台运行，不占用终端。

1. 启动服务：后端 `uvicorn` + 前端（或 `docker compose up`）
2. 打开 Dashboard：`http://localhost:3000`
3. 进入「仿真测试」页面
4. 点击「启动仿真」

仿真启动后：

- 多台服务器（web-01、api-02、db-03）每 5 秒上报指标
- 随机产生 CPU 过载、内存不足、存储紧张等场景
- 告警触发后 **AI 自动分类并执行处置**，无需人工
- 在「仿真事件流」表格中查看实时事件
- 在「总览」「告警事件」「自动化处置」页面验证数据更新

## 五、终端模拟脚本（可选）

```powershell
cd D:\shizhan
python scripts/simulate_demo.py --base-url http://localhost:8000 --interval 5
```

---

## 六、LLM 大模型接入（可选）

配置环境变量后可接入大模型增强告警分类与根因分析：

```
LLM_PROVIDER=openai
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-xxx
```

`app/services/llm_client.py` 预留了 `call_llm_for_classify` 与 `call_llm_for_analysis`，可按需接入 OpenAI、通义千问、文心一言等。

## 七、分类与 Runbook 对照表

| 告警分类 | 中文标签 | 处置动作（Demo 模拟） |
|----------|----------|------------------------|
| disk | 存储问题 | 删除过期日志释放空间；备份关键数据并归档 |
| cpu | CPU 过载 | 终止非业务相关进程降低负载；限流后台任务 |
| memory | 内存不足 | 检查内存泄漏；建议扩容或重启服务 |
| network | 网络/IO 异常 | 检查网络连通性与依赖；重试或切换备用节点 |
| app_error | 应用错误 | 查看应用日志定位根因；必要时重启服务 |
| unknown | 未知类型 | 建议人工排查 |

---

## 八、验证清单

- [ ] 健康检查返回正常
- [ ] 创建 CPU/内存/磁盘三条告警规则
- [ ] 多台服务器上报指标并触发告警
- [ ] 告警事件列表可查
- [ ] `GET /repairs/events/{id}/classify` 返回正确分类
- [ ] `POST /repairs/events/{id}/execute` 成功执行并返回 steps
- [ ] `GET /repairs` 可查看处置记录
- [ ] 前端「仿真测试」启动后事件流有更新
- [ ] Dashboard（若已启动）展示告警与处置

# API 规格（MVP）

Base URL：`http://localhost:8000`

## 1) Health

### GET `/health`
- **响应**：`{"status":"ok"}`

## 2) Ingest（Agent 上报）

### POST `/ingest/metrics`
- **用途**：上报一批 metrics points，并触发告警规则评估
- **Request**

```json
{
  "server": { "hostname": "srv-1", "os": "linux", "tags": { "env": "prod" } },
  "points": [
    { "ts": "2026-03-06T00:00:00Z", "name": "cpu_usage", "value": 0.92, "labels": { "core": "all" } }
  ]
}
```

- **Response**

```json
{ "server_id": 1, "ingested": 1, "alerts_fired": [123] }
```

### POST `/ingest/logs`
- **用途**：上报一批结构化日志
- **Request**

```json
{
  "server": { "hostname": "srv-1", "os": "linux", "tags": {} },
  "events": [
    { "ts": "2026-03-06T00:00:00Z", "level": "ERROR", "message": "db timeout", "source": "app", "fields": { "trace_id": "t1" } }
  ]
}
```

- **Response**

```json
{ "server_id": 1, "ingested": 1 }
```

## 3) Servers

### GET `/servers`
- **用途**：列出服务器资产（按 last_seen 由新到旧）

## 4) Alerts

### POST `/alerts/rules`
- **用途**：新增告警规则（指标阈值）

```json
{
  "name": "High CPU",
  "enabled": true,
  "metric_name": "cpu_usage",
  "comparator": ">",
  "threshold": 0.9,
  "for_seconds": 60,
  "severity": "critical",
  "labels": { "team": "sre" }
}
```

### GET `/alerts/rules`
- **用途**：列出规则

### GET `/alerts/events?limit=50`
- **用途**：列出最近告警事件

### GET `/alerts/events/{event_id}/analysis`
- **用途**：获取 AI 分析结果（MVP 为 stub）


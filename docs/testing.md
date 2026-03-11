# 测试与验证

## 1) 目标
- **API 正常响应**：health/ingest/alerts
- **数据一致性**：上报后可查询 servers、alerts events
- **告警逻辑**：阈值触发可产生事件

## 2) 测试策略
- **单元测试**：告警比较器（>,>=,<,<=,==）与规则评估（可后续补）
- **集成测试（目前已做）**：用 SQLite 暂存 DB 跑完整 API 流程
- **E2E（建议）**：docker compose 启动后，跑一段 agent，上报/产生告警/查询分析

## 3) 執行

```bash
cd backend
pytest -q
```

## 4) 诊断技巧
- 测试若卡在 DB：确认 `DATABASE_URL` 是否被测试 fixture 覆写到 SQLite
- 若 schema 没建：确认 FastAPI startup 有调用 `init_db()`


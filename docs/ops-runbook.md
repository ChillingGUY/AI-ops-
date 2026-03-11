# 运维 Runbook（部署 / 巡检 / 故障处理）

## 0. 目标与 SLO（建议）
- **平台可用性**：99.9%
- **告警延迟**：P95 < 30s（MVP 为同步评估；后续建议异步）
- **数据保留**：
  - Metrics：近 14~30 天（后续可下采样）
  - Logs：近 7 天热存（PostgreSQL），历史冷存（MinIO）

## 1. 部署（Docker Compose）

### 1.1 启动
在專案根目錄：

```bash
docker compose up --build -d
docker compose ps
```

### 1.2 验证
- 打开 `http://localhost:8000/health` 应回 `{"status":"ok"}`
- 打开 `http://localhost:8000/docs` 确认 OpenAPI

### 1.3 重要设置（环境变量）
Backend：
- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` / `MINIO_BUCKET`
- `LLM_PROVIDER` / `LLM_API_BASE` / `LLM_API_KEY`（未来接入）

## 2. 巡检清单（每日/每周）

### 每日
- **服务状态**：`docker compose ps` 无 unhealthy
- **API 健康**：`/health` 200
- **DB 连接数**：PostgreSQL active connections 无异常暴增
- **告警事件量**：近 1 小时 alert events 是否激增（可能代表故障或规则误报）

### 每周
- **磁盘水位**：PostgreSQL volume / MinIO volume 使用率
- **保留策略**：是否需要清理过旧数据（MVP 尚未内建 TTL job）
- **规则盘点**：告警规则是否过多/过严/重复

## 3. 备份与还原（建议）

### PostgreSQL 备份（每天）
容器外执行示例（按你的环境调整）：

```bash
docker exec -t <postgres-container> pg_dump -U aiops -d aiops > aiops_$(date +%F).sql
```

### 還原

```bash
cat aiops_2026-03-06.sql | docker exec -i <postgres-container> psql -U aiops -d aiops
```

## 4. 告警处理流程（建议 SOP）

1) **确认范围**：server_id / hostname、影响服务、开始时间  
2) **定位类型**：资源饱和 vs 依赖超时 vs 程序错误  
3) **关联数据**：
   - 同時間窗 metrics：CPU/mem/disk
   - 同時間窗 logs：error/timeout/oom
4) **修复动作**：
   - 降载/扩容（scale out）
   - 回滚部署
   - 重启服务（若可接受）
5) **复盘**：
   - 规则是否需调整
   - 是否可自动修复
   - 需要补监控/日志字段

## 5. 常见故障与处置

### 5.1 Backend 500 / 无法 ingest
- 检查 `backend` logs
- 检查 Postgres/Redis 是否 healthy
- 检查 DB 连接是否耗尽（max connections）

### 5.2 DB IO 飙高
- 确认 ingest 速率是否暴增
- 增加索引/分表/下采样（中长期）
- 先调高资源或分离磁盘（短期）

### 5.3 告警误报过多
- 调整 threshold/for_seconds
- 加入去重/抑制（maintenance window）
- 用 P95 基线而非固定阈值（后续 AI/统计模块）


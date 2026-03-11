from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LogEvent, MetricSample
from app.schemas import LogsIngestIn, MetricsIngestIn
from app.services.alert_engine import evaluate_rules_for_server
from app.services.auto_repair import execute_repair
from app.services.server_manager import upsert_server

router = APIRouter(prefix="/ingest", tags=["数据上报"])


@router.post("/metrics", summary="上报指标", description="Agent 上报一批监控指标点，并触发告警规则评估。")
def ingest_metrics(payload: MetricsIngestIn, db: Session = Depends(get_db)) -> dict:
    server = upsert_server(db, payload.server)
    count = 0
    for p in payload.points:
        db.add(
            MetricSample(
                server_id=server.id,
                ts=p.ts,
                name=p.name,
                value=p.value,
                labels=p.labels,
            )
        )
        count += 1
    db.commit()

    fired = evaluate_rules_for_server(db, server.id, now=datetime.now(timezone.utc))
    for evt in fired:
        execute_repair(db, evt.id, dry_run=False)
    db.commit()

    return {"server_id": server.id, "ingested": count, "alerts_fired": [e.id for e in fired]}


@router.post("/logs", summary="上报日志", description="Agent 上报一批结构化日志。")
def ingest_logs(payload: LogsIngestIn, db: Session = Depends(get_db)) -> dict:
    server = upsert_server(db, payload.server)
    count = 0
    for e in payload.events:
        db.add(
            LogEvent(
                server_id=server.id,
                ts=e.ts,
                level=e.level.upper(),
                message=e.message,
                source=e.source,
                fields=e.fields,
            )
        )
        count += 1
    db.commit()
    return {"server_id": server.id, "ingested": count}


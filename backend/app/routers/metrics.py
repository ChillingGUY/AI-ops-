from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MetricSample, Server

router = APIRouter(prefix="/metrics", tags=["指标"])


@router.get("/latest", summary="最新指标", description="获取各服务器在最近时间窗口内的最新资源指标（CPU/内存/磁盘）。按最新时间戳取值，优化执行后即可看到变化。")
def latest_metrics(
    db: Session = Depends(get_db),
    window_minutes: int = Query(5, ge=1, le=60, description="时间窗口（分钟）"),
) -> dict:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)

    # 按 (server_id, name) 取最新时间戳对应的 value，而非 max(value)
    subq = (
        select(
            MetricSample.server_id,
            MetricSample.name,
            func.max(MetricSample.ts).label("max_ts"),
        )
        .where(MetricSample.ts >= window_start)
        .group_by(MetricSample.server_id, MetricSample.name)
    ).subquery()
    stmt = (
        select(MetricSample.server_id, Server.hostname, MetricSample.name, MetricSample.value)
        .join(Server, Server.id == MetricSample.server_id)
        .join(
            subq,
            (MetricSample.server_id == subq.c.server_id)
            & (MetricSample.name == subq.c.name)
            & (MetricSample.ts == subq.c.max_ts),
        )
        .where(MetricSample.ts >= window_start)
    )
    result = db.execute(stmt).all()

    servers: dict[int, dict] = {}
    for server_id, hostname, name, value in result:
        s = servers.setdefault(
            server_id,
            {"server_id": server_id, "hostname": hostname, "metrics": {}},
        )
        s["metrics"][name] = float(value)

    return {"items": list(servers.values())}


@router.get("/timeseries", summary="指标时序", description="获取单指标的时间序列数据，用于图表展示。")
def metric_timeseries(
    metric_name: str = Query(..., description="指标名称，如 cpu_usage"),
    server_id: int | None = Query(None, description="服务器 ID，不填则所有服务器"),
    minutes: int = Query(10, ge=1, le=1440, description="时间范围（分钟）"),
    limit: int = Query(200, ge=1, le=1000, description="返回条数上限"),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=minutes)

    stmt = (
        select(MetricSample.ts, MetricSample.value, MetricSample.server_id)
        .where(
            MetricSample.name == metric_name,
            MetricSample.ts >= window_start,
        )
        .order_by(desc(MetricSample.ts))
        .limit(limit)
    )
    if server_id is not None:
        stmt = stmt.where(MetricSample.server_id == server_id)

    rows = db.execute(stmt).all()
    items = [
        {
            "ts": ts.isoformat(),
            "value": float(value),
            "server_id": sid,
        }
        for ts, value, sid in reversed(rows)
    ]
    return {"metric_name": metric_name, "items": items}


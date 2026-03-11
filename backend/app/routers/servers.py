from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import OptimizationLog, Server
from app.schemas import ServerOut
from app.services.resource_optimizer import execute_server_optimization, get_optimization_suggestions

router = APIRouter(prefix="/servers", tags=["服务器"])


@router.get("", response_model=list[ServerOut], summary="列出服务器", description="列出所有已注册的服务器资产，按最后上线时间倒序。")
def list_servers(db: Session = Depends(get_db)) -> list[ServerOut]:
    rows = db.scalars(select(Server).order_by(desc(Server.last_seen_at))).all()
    return [
        ServerOut(
            id=s.id,
            hostname=s.hostname,
            os=s.os,
            tags=s.tags,
            last_seen_at=s.last_seen_at,
        )
        for s in rows
    ]


@router.get(
    "/{server_id}/suggestions",
    summary="服务器优化建议",
    description="基于当前指标与近期告警，由 AI 生成优化建议（已配置 LLM 时调用大模型，否则规则兜底）。",
)
def get_server_suggestions(server_id: int, db: Session = Depends(get_db)) -> dict:
    result = get_optimization_suggestions(db, server_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post(
    "/{server_id}/optimize",
    summary="执行服务器优化",
    description="用户确认后，对服务器执行 AI 建议的优化动作（Demo 版为模拟执行）。",
)
def run_server_optimize(server_id: int, db: Session = Depends(get_db)) -> dict:
    result = execute_server_optimization(db, server_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get(
    "/optimization-logs",
    summary="优化执行日志",
    description="获取服务器优化执行日志，含优化前后指标与效果。",
)
def list_optimization_logs(
    limit: int = Query(50, description="返回条数"),
    server_id: int | None = Query(None, description="按服务器 ID 筛选"),
    db: Session = Depends(get_db),
) -> dict:
    stmt = (
        select(OptimizationLog, Server.hostname)
        .join(Server, Server.id == OptimizationLog.server_id)
        .order_by(desc(OptimizationLog.ts))
        .limit(limit)
    )
    if server_id is not None:
        stmt = stmt.where(OptimizationLog.server_id == server_id)
    rows = db.execute(stmt).all()
    items = [
        {
            "id": log.id,
            "server_id": log.server_id,
            "hostname": hostname,
            "ts": log.ts.isoformat(),
            "metrics_before": log.metrics_before,
            "metrics_after": log.metrics_after,
            "actions_count": log.actions_count,
            "summary": log.summary,
        }
        for log, hostname in rows
    ]
    return {"items": items}


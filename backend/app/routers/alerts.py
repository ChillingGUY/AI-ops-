from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AlertEvent, AlertRule, LogEvent
from app.schemas import AlertEventOut, AlertRuleIn, AlertRuleOut
from app.services.ai_analyzer import analyze_alert

router = APIRouter(prefix="/alerts", tags=["告警"])


@router.post("/rules", response_model=AlertRuleOut, summary="新增告警规则", description="创建一条指标阈值告警规则。")
def create_rule(rule_in: AlertRuleIn, db: Session = Depends(get_db)) -> AlertRuleOut:
    rule = AlertRule(**rule_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return AlertRuleOut(id=rule.id, **rule_in.model_dump())


@router.get("/rules", response_model=list[AlertRuleOut], summary="列出告警规则", description="获取所有告警规则。")
def list_rules(db: Session = Depends(get_db)) -> list[AlertRuleOut]:
    rules = db.scalars(select(AlertRule).order_by(AlertRule.id)).all()
    out: list[AlertRuleOut] = []
    for r in rules:
        out.append(
            AlertRuleOut(
                id=r.id,
                name=r.name,
                enabled=r.enabled,
                metric_name=r.metric_name,
                comparator=r.comparator,
                threshold=r.threshold,
                for_seconds=r.for_seconds,
                severity=r.severity,
                labels=r.labels,
            )
        )
    return out


@router.get("/events", response_model=list[AlertEventOut], summary="列出告警事件", description="获取最近的告警事件列表。")
def list_alert_events(limit: int = Query(50, description="返回条数"), db: Session = Depends(get_db)) -> list[AlertEventOut]:
    events = db.scalars(select(AlertEvent).order_by(desc(AlertEvent.ts)).limit(limit)).all()
    return [
        AlertEventOut(
            id=e.id,
            rule_id=e.rule_id,
            server_id=e.server_id,
            ts=e.ts,
            status=e.status,
            severity=e.severity,
            summary=e.summary,
            details=e.details,
            context=e.context,
        )
        for e in events
    ]


@router.get("/events/{event_id}/analysis", summary="告警 AI 分析", description="对指定告警事件进行 AI 根因分析，返回可能原因与处置建议。")
def analyze_event(event_id: int, db: Session = Depends(get_db)) -> dict:
    e = db.scalar(select(AlertEvent).where(AlertEvent.id == event_id))
    if not e:
        raise HTTPException(status_code=404, detail="告警事件不存在")

    recent_logs = db.scalars(
        select(LogEvent.message)
        .where(LogEvent.server_id == e.server_id)
        .order_by(desc(LogEvent.ts))
        .limit(50)
    ).all()
    metric_name = None
    if e.context and isinstance(e.context.get("metric"), dict):
        metric_name = e.context["metric"].get("name")
    analysis = analyze_alert(e.summary, e.details, recent_logs, metric_name)
    return {
        "event_id": e.id,
        "anomaly": analysis.anomaly,
        "summary": analysis.summary,
        "probable_causes": analysis.probable_causes,
        "suggestions": analysis.suggestions,
        "source": analysis.source,
    }


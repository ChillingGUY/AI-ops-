"""自动化处置 API"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AlertEvent, RepairAction
from app.schemas import AlertCategoryOut, RepairActionOut
from app.services.alert_classifier import classify_alert
from app.services.auto_repair import execute_repair, get_suggested_repairs
from app.services.automation_evaluator import evaluate_repair_action, evaluate_alert_event_repairs

router = APIRouter(prefix="/repairs", tags=["自动化处置"])


@router.get(
    "",
    response_model=list[RepairActionOut],
    summary="列出处置记录",
    description="获取所有自动化处置记录。",
)
def list_repairs(
    limit: int = Query(50, description="返回条数"),
    db: Session = Depends(get_db),
) -> list[RepairActionOut]:
    rows = db.scalars(
        select(RepairAction).order_by(desc(RepairAction.ts)).limit(limit)
    ).all()
    return [
        RepairActionOut(
            id=r.id,
            alert_event_id=r.alert_event_id,
            ts=r.ts,
            action_type=r.action_type,
            target=r.target,
            status=r.status,
            output=r.output,
        )
        for r in rows
    ]


@router.get(
    "/events/{event_id}/classify",
    response_model=AlertCategoryOut,
    summary="告警分类",
    description="对指定告警进行 AI 分类（存储/CPU/内存/网络/应用错误）。",
)
def classify_alert_event(event_id: int, db: Session = Depends(get_db)) -> AlertCategoryOut:
    evt = db.get(AlertEvent, event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="告警事件不存在")
    metric_name = None
    if evt.context and isinstance(evt.context.get("metric"), dict):
        metric_name = evt.context["metric"].get("name")
    cat = classify_alert(evt.summary, metric_name, evt.details)
    return AlertCategoryOut(category=cat.category, label=cat.label, confidence=cat.confidence)


@router.post(
    "/events/{event_id}/execute",
    summary="执行自动化处置",
    description="根据告警分类执行对应 Runbook（存储：删除日志并备份；CPU：终止非业务进程等）。Demo 版为模拟执行。",
)
def execute_for_event(
    event_id: int,
    dry_run: bool = Query(False, description="仅预览，不实际执行"),
    db: Session = Depends(get_db),
) -> dict:
    evt = db.get(AlertEvent, event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="告警事件不存在")
    cat, steps = get_suggested_repairs(evt)
    actions = execute_repair(db, event_id, dry_run=dry_run)
    return {
        "event_id": event_id,
        "category": cat.category,
        "label": cat.label,
        "dry_run": dry_run,
        "steps": [{"action_type": a.action_type, "target": a.target, "output": a.output} for a in actions],
    }


@router.get(
    "/{repair_id}/evaluation",
    summary="单次处置效果评估",
    description="对指定处置动作进行 AI 效果评估，给出评分与改进建议（已配置 LLM 时调用大模型）。",
)
def evaluate_repair(repair_id: int, db: Session = Depends(get_db)) -> dict:
    result = evaluate_repair_action(db, repair_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get(
    "/events/{event_id}/evaluation",
    summary="告警处置整体评估",
    description="评估某告警事件下所有处置动作的整体效果，给出评分与改进建议。",
)
def evaluate_event_repairs(event_id: int, db: Session = Depends(get_db)) -> dict:
    result = evaluate_alert_event_repairs(db, event_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result

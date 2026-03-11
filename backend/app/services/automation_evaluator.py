"""自动化运维评估：评估单次或整体自动处置效果，通过 LLM 给出改进建议。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AlertEvent, RepairAction
from app.services.alert_classifier import classify_alert
from app.services.llm_client import llm_automation_evaluation, _is_llm_configured


def evaluate_repair_action(db: Session, repair_id: int) -> dict:
    """
    评估单次处置动作的效果。
    已配置 LLM 时调用大模型，否则返回规则兜底。
    """
    ra = db.get(RepairAction, repair_id)
    if not ra:
        return {"error": "处置记录不存在"}
    evt = db.get(AlertEvent, ra.alert_event_id)
    if not evt:
        return {"error": "关联告警不存在"}
    metric_name = None
    if evt.context and isinstance(evt.context.get("metric"), dict):
        metric_name = evt.context["metric"].get("name")
    cat = classify_alert(evt.summary, metric_name, evt.details)
    actions = [ra.target]
    outcome = ra.status
    context = f"告警: {evt.summary}，动作: {ra.target}，输出: {ra.output or '无'}"
    if _is_llm_configured():
        result = llm_automation_evaluation(
            cat.label, actions, outcome, context
        )
        if result:
            return {"source": "llm", "repair_id": repair_id, **result}
    return {
        "source": "rule",
        "repair_id": repair_id,
        "score": 75 if ra.status == "succeeded" else 50,
        "evaluation": f"处置状态: {ra.status}，建议根据实际业务验证效果并优化 Runbook。",
        "improvements": [
            "增加处置前的风险检查",
            "记录更详细的执行日志便于复盘",
            "考虑增加人工确认环节（高危操作）",
        ],
    }


def evaluate_alert_event_repairs(db: Session, alert_event_id: int) -> dict:
    """
    评估某告警事件下所有处置动作的整体效果。
    """
    evt = db.get(AlertEvent, alert_event_id)
    if not evt:
        return {"error": "告警事件不存在"}
    repairs = db.query(RepairAction).where(RepairAction.alert_event_id == alert_event_id).all()
    if not repairs:
        return {"error": "该告警无处置记录"}
    actions = [f"{r.target}({r.status})" for r in repairs]
    outcome = "全部成功" if all(r.status == "succeeded" for r in repairs) else "部分失败"
    metric_name = None
    if evt.context and isinstance(evt.context.get("metric"), dict):
        metric_name = evt.context["metric"].get("name")
    cat = classify_alert(evt.summary, metric_name, evt.details)
    context = f"告警: {evt.summary}，共 {len(repairs)} 个动作"
    if _is_llm_configured():
        result = llm_automation_evaluation(cat.label, actions, outcome, context)
        if result:
            return {"source": "llm", "event_id": alert_event_id, "actions_count": len(repairs), **result}
    return {
        "source": "rule",
        "event_id": alert_event_id,
        "actions_count": len(repairs),
        "score": 80 if outcome == "全部成功" else 60,
        "evaluation": f"共执行 {len(repairs)} 个动作，结果: {outcome}。",
        "improvements": ["优化 Runbook 顺序", "增加失败重试机制"],
    }

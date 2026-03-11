"""AI 自动化处置引擎：根据告警分类执行对应 Runbook（Demo 版为模拟执行）。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AlertEvent, RepairAction
from app.services.alert_classifier import AlertCategory, classify_alert


@dataclass
class RepairStep:
    """单步处置动作"""
    action_type: str
    target: str
    description: str


# 按分类预定义的 Runbook
RUNBOOKS: dict[str, list[RepairStep]] = {
    "disk": [
        RepairStep("runbook", "cleanup_logs", "删除过期日志释放空间"),
        RepairStep("runbook", "backup_and_archive", "备份关键数据并归档"),
    ],
    "cpu": [
        RepairStep("runbook", "kill_non_business_process", "终止非业务相关进程降低负载"),
        RepairStep("runbook", "throttle_background_jobs", "限流后台任务"),
    ],
    "memory": [
        RepairStep("runbook", "check_memory_leak", "检查内存泄漏"),
        RepairStep("runbook", "suggest_scale", "建议扩容或重启服务"),
    ],
    "network": [
        RepairStep("runbook", "check_connectivity", "检查网络连通性与依赖"),
        RepairStep("runbook", "retry_or_fallback", "重试或切换备用节点"),
    ],
    "app_error": [
        RepairStep("runbook", "check_logs", "查看应用日志定位根因"),
        RepairStep("runbook", "restart_service", "必要时重启服务"),
    ],
    "unknown": [
        RepairStep("runbook", "manual_review", "建议人工排查"),
    ],
}


def get_suggested_repairs(alert_event: AlertEvent) -> tuple[AlertCategory, list[RepairStep]]:
    """根据告警事件获取建议的处置步骤。"""
    metric_name = None
    if alert_event.context and isinstance(alert_event.context.get("metric"), dict):
        metric_name = alert_event.context["metric"].get("name")
    cat = classify_alert(alert_event.summary, metric_name, alert_event.details)
    steps = RUNBOOKS.get(cat.category, RUNBOOKS["unknown"])
    return cat, steps


def execute_repair(
    db: Session,
    alert_event_id: int,
    dry_run: bool = False,
) -> list[RepairAction]:
    """
    对指定告警执行自动化处置（Demo 版：仅记录到 repair_actions，不执行真实系统命令）。
    dry_run=True 时只返回将执行的步骤，不写入库。
    """
    evt = db.get(AlertEvent, alert_event_id)
    if not evt:
        return []

    cat, steps = get_suggested_repairs(evt)
    actions: list[RepairAction] = []

    for s in steps:
        if dry_run:
            # 不落库，仅构造对象用于返回
            a = RepairAction(
                alert_event_id=alert_event_id,
                action_type=s.action_type,
                target=s.target,
                status="queued",
                output=f"[模拟] {s.description}",
            )
            actions.append(a)
        else:
            # Demo：模拟执行成功
            ra = RepairAction(
                alert_event_id=alert_event_id,
                action_type=s.action_type,
                target=s.target,
                status="succeeded",
                output=f"[Demo 模拟执行] {s.description}，分类={cat.label}",
            )
            db.add(ra)
            db.flush()
            actions.append(ra)

    if not dry_run:
        db.commit()

    return actions

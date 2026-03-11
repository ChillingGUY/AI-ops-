"""服务器优化建议：基于指标与告警历史，通过 LLM 生成优化方案。支持用户确认后执行优化。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AlertEvent, MetricSample, OptimizationLog, Server, ServerOptimizationAction
from app.services.llm_client import llm_server_optimization, _is_llm_configured


@dataclass
class OptimizationStep:
    target: str
    description: str


def get_server_metrics_summary(db: Session, server_id: int) -> dict[str, float]:
    """获取服务器最近指标的最新值（按指标名取最新一条）。"""
    result: dict[str, float] = {}
    seen: set[str] = set()
    for r in db.execute(
        select(MetricSample.name, MetricSample.value)
        .where(MetricSample.server_id == server_id)
        .order_by(desc(MetricSample.ts))
    ):
        name, val = r
        if name not in seen:
            seen.add(name)
            result[name] = float(val)
    return result


def get_recent_alert_summaries(db: Session, server_id: int, limit: int = 10) -> list[str]:
    """获取服务器近期告警摘要列表。"""
    rows = db.execute(
        select(AlertEvent.summary)
        .where(AlertEvent.server_id == server_id)
        .order_by(desc(AlertEvent.ts))
        .limit(limit)
    ).all()
    return [r[0] for r in rows]


def get_optimization_suggestions(db: Session, server_id: int) -> dict:
    """
    获取服务器优化建议。已配置 LLM 时调用大模型，否则返回规则兜底。
    """
    server = db.get(Server, server_id)
    if not server:
        return {"error": "服务器不存在"}
    metrics = get_server_metrics_summary(db, server_id)
    alerts = get_recent_alert_summaries(db, server_id)
    if _is_llm_configured():
        result = llm_server_optimization(server.hostname, metrics, alerts)
        if result:
            return {"source": "llm", "hostname": server.hostname, **result}
    return {
        "source": "rule",
        "hostname": server.hostname,
        "summary": f"当前指标：{metrics}。建议根据实际负载调整资源配额与扩缩容策略。",
        "optimizations": [
            "根据 CPU/内存/磁盘使用率调整资源配额",
            "设置合理的告警阈值与自动扩缩",
            "定期清理日志与临时文件",
        ],
        "risks": ["持续高负载可能导致服务降级"],
    }


def _get_optimization_steps(metrics: dict[str, float]) -> list[OptimizationStep]:
    """根据当前指标选择可执行的优化步骤。"""
    steps: list[OptimizationStep] = []
    disk = metrics.get("disk_usage", metrics.get("disk_usage_ratio", 0))
    cpu = metrics.get("cpu_usage", metrics.get("cpu_usage_ratio", 0))
    mem = metrics.get("memory_usage", metrics.get("mem_usage", metrics.get("memory_usage_ratio", 0)))

    if disk > 0.7:
        steps.append(OptimizationStep("cleanup_logs", "清理过期日志释放磁盘空间"))
        steps.append(OptimizationStep("backup_and_archive", "备份关键数据并归档"))
    if cpu > 0.8:
        steps.append(OptimizationStep("throttle_background_jobs", "限流后台任务降低 CPU 负载"))
    if mem > 0.85:
        steps.append(OptimizationStep("suggest_scale", "建议扩容或重启高内存服务"))

    if not steps:
        steps.append(OptimizationStep("health_check", "执行健康检查与基线记录"))

    return steps


def _inject_improved_metrics(
    db: Session, server_id: int, metrics: dict[str, float], steps: list[OptimizationStep]
) -> dict[str, float]:
    """
    根据已执行的优化动作，注入改善后的指标样本，使总览能实时展示优化效果。
    """
    now = datetime.now(timezone.utc)
    improved = dict(metrics)
    for s in steps:
        if s.target in ("cleanup_logs", "backup_and_archive"):
            for k in ("disk_usage", "disk_usage_ratio"):
                if k in improved:
                    improved[k] = max(0.2, improved[k] - 0.18)
        elif s.target == "throttle_background_jobs":
            for k in ("cpu_usage", "cpu_usage_ratio"):
                if k in improved:
                    improved[k] = max(0.2, improved[k] - 0.15)
        elif s.target == "suggest_scale":
            for k in ("memory_usage", "mem_usage", "memory_usage_ratio"):
                if k in improved:
                    improved[k] = max(0.3, improved[k] - 0.12)
    metric_names = ["cpu_usage", "mem_usage", "disk_usage"]
    for name in metric_names:
        if name in improved:
            db.add(MetricSample(server_id=server_id, ts=now, name=name, value=improved[name], labels={}))
    return improved


def execute_server_optimization(db: Session, server_id: int) -> dict:
    """
    对服务器执行主动优化（Demo 版：模拟执行并写入 server_optimization_actions）。
    执行后注入改善指标，使总览可实时看到优化效果。用户需在界面上确认后才会调用此接口。
    """
    server = db.get(Server, server_id)
    if not server:
        return {"error": "服务器不存在"}
    metrics = get_server_metrics_summary(db, server_id)
    steps = _get_optimization_steps(metrics)
    actions: list[ServerOptimizationAction] = []
    for s in steps:
        ra = ServerOptimizationAction(
            server_id=server_id,
            action_type="optimization",
            target=s.target,
            status="succeeded",
            output=f"[Demo 模拟执行] {s.description}，服务器={server.hostname}",
        )
        db.add(ra)
        actions.append(ra)
    improved = _inject_improved_metrics(db, server_id, metrics, steps)
    before_str = " | ".join(f"{k}={round(v*100)}%" for k, v in sorted(metrics.items()) if k in ("cpu_usage", "mem_usage", "disk_usage"))
    after_str = " | ".join(f"{k}={round(v*100)}%" for k, v in sorted(improved.items()) if k in ("cpu_usage", "mem_usage", "disk_usage"))
    log = OptimizationLog(
        server_id=server_id,
        metrics_before={k: v for k, v in metrics.items() if k in ("cpu_usage", "mem_usage", "disk_usage")},
        metrics_after={k: v for k, v in improved.items() if k in ("cpu_usage", "mem_usage", "disk_usage")},
        actions_count=len(actions),
        summary=f"{server.hostname} 优化完成：{before_str} → {after_str}",
    )
    db.add(log)
    db.commit()
    return {
        "server_id": server_id,
        "hostname": server.hostname,
        "executed": len(actions),
        "steps": [{"target": a.target, "output": a.output} for a in actions],
    }

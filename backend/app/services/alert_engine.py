from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AlertEvent, AlertRule, MetricSample


def _compare(value: float, comparator: str, threshold: float) -> bool:
    if comparator == ">":
        return value > threshold
    if comparator == ">=":
        return value >= threshold
    if comparator == "<":
        return value < threshold
    if comparator == "<=":
        return value <= threshold
    if comparator == "==":
        return value == threshold
    raise ValueError(f"Unsupported comparator: {comparator}")


def evaluate_rules_for_server(db: Session, server_id: int, now: datetime | None = None) -> list[AlertEvent]:
    now = now or datetime.now(timezone.utc)
    rules = db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))).all()
    fired: list[AlertEvent] = []

    for rule in rules:
        window_start = now - timedelta(seconds=rule.for_seconds)
        latest = db.scalar(
            select(MetricSample)
            .where(
                MetricSample.server_id == server_id,
                MetricSample.name == rule.metric_name,
                MetricSample.ts >= window_start,
            )
            .order_by(desc(MetricSample.ts))
            .limit(1)
        )
        if not latest:
            continue

        is_bad = _compare(float(latest.value), rule.comparator, float(rule.threshold))
        if not is_bad:
            continue

        evt = AlertEvent(
            rule_id=rule.id,
            server_id=server_id,
            ts=now,
            status="firing",
            severity=rule.severity,
            summary=f"{rule.name}: {rule.metric_name} {rule.comparator} {rule.threshold}",
            details=f"latest={latest.value} at {latest.ts.isoformat()}",
            context={"metric": {"name": latest.name, "value": latest.value, "ts": latest.ts.isoformat()}},
        )
        db.add(evt)
        db.flush()
        fired.append(evt)

    return fired


from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    os: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metrics: Mapped[list["MetricSample"]] = relationship(back_populates="server")
    logs: Mapped[list["LogEvent"]] = relationship(back_populates="server")


class MetricSample(Base):
    __tablename__ = "metric_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[float] = mapped_column()
    labels: Mapped[dict] = mapped_column(JSON, default=dict)

    server: Mapped["Server"] = relationship(back_populates="metrics")


Index("idx_metric_server_name_ts", MetricSample.server_id, MetricSample.name, MetricSample.ts)


class LogEvent(Base):
    __tablename__ = "log_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String(128), default="agent")
    level: Mapped[str] = mapped_column(String(16), index=True)
    message: Mapped[str] = mapped_column(Text)
    fields: Mapped[dict] = mapped_column(JSON, default=dict)

    server: Mapped["Server"] = relationship(back_populates="logs")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(default=True)

    metric_name: Mapped[str] = mapped_column(String(128), index=True)
    comparator: Mapped[str] = mapped_column(String(8), default=">")
    threshold: Mapped[float] = mapped_column()
    for_seconds: Mapped[int] = mapped_column(Integer, default=60)
    severity: Mapped[str] = mapped_column(String(16), default="warning")

    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(16), default="firing")  # firing/resolved
    severity: Mapped[str] = mapped_column(String(16), default="warning")
    summary: Mapped[str] = mapped_column(String(256))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)


Index("idx_alert_rule_server_ts", AlertEvent.rule_id, AlertEvent.server_id, AlertEvent.ts)


class RepairAction(Base):
    __tablename__ = "repair_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_event_id: Mapped[int] = mapped_column(ForeignKey("alert_events.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action_type: Mapped[str] = mapped_column(String(32), default="runbook")
    target: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued/running/succeeded/failed
    output: Mapped[str | None] = mapped_column(Text, nullable=True)


class ServerOptimizationAction(Base):
    """服务器主动优化执行记录（用户确认后执行）"""
    __tablename__ = "server_optimization_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action_type: Mapped[str] = mapped_column(String(32), default="optimization")
    target: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="succeeded")
    output: Mapped[str | None] = mapped_column(Text, nullable=True)


class OptimizationLog(Base):
    """优化执行日志（每次优化运行一条，含优化前后指标与效果）"""
    __tablename__ = "optimization_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metrics_before: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_after: Mapped[dict] = mapped_column(JSON, default=dict)
    actions_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(String(512))


"""7x24 仿真服务：后台模拟多服务器上报，告警自动由 AI 处置，无需人工。已优化服务器不再进行测试处理。"""
from __future__ import annotations

import random
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_sessionmaker
from app.models import AlertRule, MetricSample, Server, ServerOptimizationAction
from app.services.alert_engine import evaluate_rules_for_server
from app.services.auto_repair import execute_repair
from app.services.server_manager import upsert_server
from app.schemas import ServerUpsert

OPTIMIZATION_COOLDOWN_MINUTES = 30

SERVERS = [
    {"hostname": "web-01", "os": "linux", "tags": {"env": "prod", "role": "web"}},
    {"hostname": "api-02", "os": "linux", "tags": {"env": "prod", "role": "api"}},
    {"hostname": "db-03", "os": "linux", "tags": {"env": "prod", "role": "db"}},
]

SCENARIOS = [
    {"name": "正常", "cpu": 0.3, "mem": 0.5, "disk": 0.6, "weight": 70},
    {"name": "CPU过载", "cpu": 0.95, "mem": 0.5, "disk": 0.6, "weight": 10},
    {"name": "内存不足", "cpu": 0.4, "mem": 0.92, "disk": 0.6, "weight": 10},
    {"name": "存储紧张", "cpu": 0.4, "mem": 0.5, "disk": 0.93, "weight": 10},
]


class SimulationState:
    running = False
    cycle = 0
    last_events: list[dict[str, Any]] = []
    _lock = threading.Lock()

    @classmethod
    def add_event(cls, ev: dict[str, Any]) -> None:
        with cls._lock:
            cls.last_events.insert(0, ev)
            cls.last_events = cls.last_events[:50]

    @classmethod
    def get_events(cls) -> list[dict[str, Any]]:
        with cls._lock:
            return list(cls.last_events)


state = SimulationState()


def _get_recently_optimized_hostnames(db: Session) -> set[str]:
    """获取近期（30分钟内）执行过优化的服务器 hostname 集合，仿真时跳过这些服务器。"""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=OPTIMIZATION_COOLDOWN_MINUTES)
    rows = (
        db.execute(
            select(Server.hostname)
            .join(ServerOptimizationAction, ServerOptimizationAction.server_id == Server.id)
            .where(ServerOptimizationAction.ts >= cutoff)
            .distinct()
        )
    ).all()
    return {r[0] for r in rows}


def _ensure_rules(db: Session) -> None:
    existing = {r.name for r in db.query(AlertRule).all()}
    rules = [
        {"name": "CPU 过高", "metric_name": "cpu_usage", "comparator": ">", "threshold": 0.9, "severity": "critical"},
        {"name": "内存过高", "metric_name": "mem_usage", "comparator": ">", "threshold": 0.9, "severity": "critical"},
        {"name": "磁盘过高", "metric_name": "disk_usage", "comparator": ">", "threshold": 0.85, "severity": "warning"},
    ]
    for r in rules:
        if r["name"] not in existing:
            db.add(AlertRule(**r))
    db.commit()


def _run_one_cycle() -> dict[str, Any]:
    db = get_sessionmaker()()
    try:
        _ensure_rules(db)
        excluded = _get_recently_optimized_hostnames(db)
        eligible = [s for s in SERVERS if s["hostname"] not in excluded]
        if not eligible:
            return {
                "ts": datetime.now(timezone.utc).isoformat(),
                "server": "-",
                "scenario": "跳过（已优化）",
                "alerts": [],
                "skipped": True,
            }
        server_dict = random.choice(eligible)
        scenario = random.choices(SCENARIOS, weights=[s["weight"] for s in SCENARIOS], k=1)[0]
        server = upsert_server(db, ServerUpsert(**server_dict))
        now = datetime.now(timezone.utc)
        ts = now.isoformat()
        points = [
            (scenario["cpu"], "cpu_usage"),
            (scenario["mem"], "mem_usage"),
            (scenario["disk"], "disk_usage"),
        ]
        for val, name in points:
            db.add(MetricSample(server_id=server.id, ts=now, name=name, value=val, labels={}))
        db.commit()
        fired = evaluate_rules_for_server(db, server.id, now=now)
        for evt in fired:
            execute_repair(db, evt.id, dry_run=False)
        db.commit()
        ev = {
            "ts": ts,
            "server": server_dict["hostname"],
            "scenario": scenario["name"],
            "alerts": [e.id for e in fired],
            "auto_repaired": len(fired),
        }
        return ev
    finally:
        db.close()


def _run_loop(interval: float) -> None:
    import time
    state.cycle = 0
    while state.running:
        try:
            ev = _run_one_cycle()
            state.cycle += 1
            state.add_event(ev)
        except Exception:
            pass
        for _ in range(max(1, int(interval))):
            if not state.running:
                break
            time.sleep(1)


_thread: threading.Thread | None = None


def start_simulation(interval: float = 5.0) -> bool:
    global _thread
    if state.running:
        return False
    state.running = True
    _thread = threading.Thread(target=_run_loop, args=(interval,), daemon=True)
    _thread.start()
    return True


def stop_simulation() -> bool:
    state.running = False
    return True


def get_status() -> dict[str, Any]:
    return {
        "running": state.running,
        "cycle": state.cycle,
        "last_events": state.get_events(),
    }

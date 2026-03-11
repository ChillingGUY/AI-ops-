from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import psutil
import requests


BACKEND_URL = os.getenv("AIOPS_BACKEND_URL", "http://localhost:8000")
HOSTNAME = os.getenv("AIOPS_HOSTNAME", os.uname().nodename)
OS_NAME = os.getenv("AIOPS_OS", "linux")
INTERVAL_SEC = int(os.getenv("AIOPS_INTERVAL_SEC", "10"))


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_metrics() -> list[dict]:
    cpu = psutil.cpu_percent(interval=None) / 100.0
    vm = psutil.virtual_memory()
    du = psutil.disk_usage("/")
    return [
        {"ts": _ts(), "name": "cpu_usage", "value": float(cpu), "labels": {}},
        {"ts": _ts(), "name": "mem_usage", "value": float(vm.percent / 100.0), "labels": {}},
        {"ts": _ts(), "name": "disk_usage", "value": float(du.percent / 100.0), "labels": {"mount": "/"}},
    ]


def send_metrics(points: list[dict]) -> None:
    payload = {"server": {"hostname": HOSTNAME, "os": OS_NAME, "tags": {}}, "points": points}
    r = requests.post(f"{BACKEND_URL}/ingest/metrics", json=payload, timeout=10)
    r.raise_for_status()


def send_log(level: str, message: str, fields: dict | None = None) -> None:
    payload = {
        "server": {"hostname": HOSTNAME, "os": OS_NAME, "tags": {}},
        "events": [
            {
                "ts": _ts(),
                "level": level,
                "message": message,
                "source": "agent",
                "fields": fields or {},
            }
        ],
    }
    r = requests.post(f"{BACKEND_URL}/ingest/logs", json=payload, timeout=10)
    r.raise_for_status()


def main() -> None:
    send_log("INFO", "agent started", {"interval_sec": INTERVAL_SEC})
    while True:
        try:
            send_metrics(collect_metrics())
        except Exception as e:  # noqa: BLE001
            try:
                send_log("ERROR", f"metrics send failed: {e}")
            except Exception:
                pass
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()


from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import create_app


def test_ingest_metrics_and_fire_alert() -> None:
    app = create_app()
    with TestClient(app) as client:
        rule = {
            "name": "High CPU",
            "enabled": True,
            "metric_name": "cpu_usage",
            "comparator": ">",
            "threshold": 0.9,
            "for_seconds": 60,
            "severity": "critical",
            "labels": {"team": "sre"},
        }
        r = client.post("/alerts/rules", json=rule)
        assert r.status_code == 200

        payload = {
            "server": {"hostname": "srv-1", "os": "linux", "tags": {"env": "dev"}},
            "points": [
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "name": "cpu_usage",
                    "value": 0.95,
                    "labels": {"core": "all"},
                }
            ],
        }
        r2 = client.post("/ingest/metrics", json=payload)
        assert r2.status_code == 200
        body = r2.json()
        assert body["ingested"] == 1
        assert isinstance(body["alerts_fired"], list)

        r3 = client.get("/alerts/events?limit=10")
        assert r3.status_code == 200
        events = r3.json()
        assert len(events) >= 1
        assert events[0]["summary"].startswith("High CPU")


def test_ingest_logs() -> None:
    app = create_app()
    with TestClient(app) as client:
        payload = {
            "server": {"hostname": "srv-logs", "os": "linux", "tags": {}},
            "events": [
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "level": "ERROR",
                    "message": "database timeout",
                    "source": "app",
                    "fields": {"trace_id": "t1"},
                }
            ],
        }
        r = client.post("/ingest/logs", json=payload)
        assert r.status_code == 200
        assert r.json()["ingested"] == 1


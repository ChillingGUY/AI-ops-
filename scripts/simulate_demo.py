#!/usr/bin/env python3
"""
7x24 模拟脚本：模拟多台服务器/应用持续上报，触发各类告警，并演示 AI 分类与自动化处置。

用法：
    python scripts/simulate_demo.py --base-url http://localhost:8000 [--duration 60] [--interval 5]

--duration: 运行秒数，0 表示无限（Ctrl+C 退出）
--interval: 上报间隔秒数
"""
from __future__ import annotations

import argparse
import random
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("请安装: pip install httpx")
    raise

# 默认多台服务器
SERVERS = [
    {"hostname": "web-srv-01", "os": "linux", "tags": {"env": "prod", "role": "web"}},
    {"hostname": "api-srv-02", "os": "linux", "tags": {"env": "prod", "role": "api"}},
    {"hostname": "db-srv-03", "os": "linux", "tags": {"env": "prod", "role": "db"}},
    {"hostname": "cache-srv-04", "os": "linux", "tags": {"env": "prod", "role": "cache"}},
]

# 模拟不同告警类型：偶尔制造超阈值
SCENARIOS = [
    {"name": "正常", "cpu": 0.3, "mem": 0.5, "disk": 0.6},
    {"name": "CPU 过载", "cpu": 0.95, "mem": 0.5, "disk": 0.6},
    {"name": "内存不足", "cpu": 0.4, "mem": 0.92, "disk": 0.6},
    {"name": "存储紧张", "cpu": 0.4, "mem": 0.5, "disk": 0.93},
]


def ensure_rules(client: httpx.Client, base: str) -> None:
    """确保告警规则存在"""
    r = client.get(f"{base}/alerts/rules")
    if r.status_code != 200:
        return
    rules = r.json()
    names = {x["name"] for x in rules}

    to_create = [
        {"name": "CPU 过高", "metric_name": "cpu_usage", "comparator": ">", "threshold": 0.9, "severity": "critical"},
        {"name": "内存过高", "metric_name": "mem_usage", "comparator": ">", "threshold": 0.9, "severity": "critical"},
        {"name": "磁盘过高", "metric_name": "disk_usage", "comparator": ">", "threshold": 0.85, "severity": "warning"},
    ]
    for rule in to_create:
        if rule["name"] not in names:
            client.post(f"{base}/alerts/rules", json=rule)
            print(f"  [规则] 创建: {rule['name']}")


def ingest_metrics(client: httpx.Client, base: str, server: dict, scenario: dict) -> list[int]:
    """上报指标，返回触发的告警 ID"""
    ts = datetime.now(timezone.utc).isoformat()
    points = [
        {"ts": ts, "name": "cpu_usage", "value": scenario["cpu"], "labels": {}},
        {"ts": ts, "name": "mem_usage", "value": scenario["mem"], "labels": {}},
        {"ts": ts, "name": "disk_usage", "value": scenario["disk"], "labels": {"mount": "/"}},
    ]
    payload = {"server": server, "points": points}
    r = client.post(f"{base}/ingest/metrics", json=payload)
    if r.status_code != 200:
        return []
    data = r.json()
    return data.get("alerts_fired", [])


def ingest_log(client: httpx.Client, base: str, server: dict, level: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "server": server,
        "events": [{"ts": ts, "level": level, "message": msg, "source": "sim"}],
    }
    client.post(f"{base}/ingest/logs", json=payload)


def run(base_url: str, duration: int, interval: int) -> None:
    client = httpx.Client(timeout=15.0)
    base = base_url.rstrip("/")
    print(f"模拟 7x24 监控 | 目标={base} | 间隔={interval}s | 时长={'无限' if duration <= 0 else f'{duration}s'}")

    # 健康检查
    r = client.get(f"{base}/health")
    if r.status_code != 200:
        print("健康检查失败，请确保后端已启动")
        return
    print("健康检查 OK")

    ensure_rules(client, base)
    start = time.time()
    cycle = 0

    try:
        while True:
            cycle += 1
            server = random.choice(SERVERS)
            scenario = random.choices(SCENARIOS, weights=[70, 10, 10, 10], k=1)[0]

            fired = ingest_metrics(client, base, server, scenario)
            if fired:
                print(f"  [{cycle}] {server['hostname']} | {scenario['name']} | 告警: {fired}")

                # 对第一个告警执行自动化处置
                eid = fired[0]
                exec_r = client.post(f"{base}/repairs/events/{eid}/execute?dry_run=false")
                if exec_r.status_code == 200:
                    j = exec_r.json()
                    print(f"          → 分类: {j['label']} | 处置: {len(j['steps'])} 步")
            else:
                print(f"  [{cycle}] {server['hostname']} | {scenario['name']} | OK")

            if duration > 0 and (time.time() - start) >= duration:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n用户中断")

    print("模拟结束")


def main() -> None:
    parser = argparse.ArgumentParser(description="AIOps 7x24 模拟")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API 地址")
    parser.add_argument("--duration", type=int, default=0, help="运行秒数，0=无限")
    parser.add_argument("--interval", type=int, default=5, help="上报间隔秒")
    args = parser.parse_args()
    run(args.base_url, args.duration, args.interval)


if __name__ == "__main__":
    main()

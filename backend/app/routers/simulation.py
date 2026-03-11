"""仿真测试 API"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.simulation import get_status, start_simulation, stop_simulation

router = APIRouter(prefix="/simulation", tags=["仿真测试"])


@router.get(
    "/status",
    summary="仿真状态",
    description="获取当前仿真运行状态与最近事件流。",
)
def simulation_status() -> dict:
    return get_status()


@router.post(
    "/start",
    summary="启动仿真",
    description="后台启动 7x24 仿真，多服务器上报，告警由 AI 自动处置，无需人工。",
)
def simulation_start(
    interval: float = Query(5.0, description="上报间隔（秒）"),
) -> dict:
    ok = start_simulation(interval=interval)
    return {"started": ok, "message": "仿真已启动" if ok else "仿真已在运行中"}


@router.post(
    "/stop",
    summary="停止仿真",
    description="停止后台仿真。",
)
def simulation_stop() -> dict:
    stop_simulation()
    return {"stopped": True, "message": "仿真已停止"}

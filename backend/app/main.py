from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers.alerts import router as alerts_router
from app.routers.health import router as health_router
from app.routers.ingest import router as ingest_router
from app.routers.servers import router as servers_router
from app.routers.metrics import router as metrics_router
from app.routers.repairs import router as repairs_router
from app.routers.settings import router as settings_router
from app.routers.simulation import router as simulation_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIOps 智能运维平台 API",
        description="智能运维平台后端接口文档，包含健康检查、指标上报、日志上报、服务器管理、告警规则与事件、指标查询等功能。",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(servers_router)
    app.include_router(alerts_router)
    app.include_router(metrics_router)
    app.include_router(repairs_router)
    app.include_router(settings_router)
    app.include_router(simulation_router)

    return app


app = create_app()


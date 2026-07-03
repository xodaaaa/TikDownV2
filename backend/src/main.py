import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.core.auth import handle_force_reset
from src.core.circuit_breaker import CircuitBreaker
from src.core.disk_monitor import DiskMonitor
from src.core.download_engine import DownloadEngine
from src.core.network_monitor import NetworkMonitor
from src.core.task_queue import APSchedulerQueue
from src.db.session import init_db, async_session_factory

from src.api.routes.system import write_log_to_buffer


def _json_serializer_for_buffer(logger_name, method_name, event_dict):
    import json
    write_log_to_buffer(event_dict)
    return json.dumps(event_dict, default=str)


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(serializer=_json_serializer_for_buffer),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("tikdown")

# Global services
download_engine = DownloadEngine()
circuit_breaker = CircuitBreaker()
network_monitor = NetworkMonitor()
disk_monitor = DiskMonitor()
task_queue = APSchedulerQueue()

from src.api.routes.system import public_router, router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup")

    # Ensure data directories exist
    Path(settings.VIDEOS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.BACKUPS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

    # Init database
    await init_db()
    logger.info("database_initialized")

    # Handle FORCE_RESET
    async with async_session_factory() as db:
        await handle_force_reset(db)
        logger.info("force_reset_handled")

    # Clean orphan jobs
    task_queue.clear_jobs()
    logger.info("orphan_jobs_cleaned")

    # Start task queue scheduler
    task_queue.start()
    logger.info("task_queue_started")

    yield

    # Shutdown
    logger.info("app_shutdown")
    await task_queue.shutdown(wait=True)
    await network_monitor.stop()
    await disk_monitor.stop()
    logger.info("app_shutdown_complete")


app = FastAPI(
    title="TikDown",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url=None,
)

# GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1024)

# CORS (dev only)
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register routers in correct order (§6.7)
# 1. Health (public, no auth) first
app.include_router(public_router)

# 2. System routes (with auth)
app.include_router(system_router)

# 3. Auth routes
from src.api.routes.auth import router as auth_router
app.include_router(auth_router)

# 4. Accounts routes
from src.api.routes.accounts import router as accounts_router
app.include_router(accounts_router)

# 5. Videos routes
from src.api.routes.videos import router as videos_router
app.include_router(videos_router)

# 6. Cookies routes
from src.api.routes.cookies import router as cookies_router
app.include_router(cookies_router)

# 7. Monitor routes (inject service reference)
from src.api.routes.monitor import router as monitor_router, set_monitor_service
from src.services.monitor import MonitorService

monitor_service = MonitorService(
    download_engine=download_engine,
    task_queue=task_queue,
    circuit_breaker=circuit_breaker,
    network_monitor=network_monitor,
    disk_monitor=disk_monitor,
)

from src.api.routes.events import push_event_to_sse
monitor_service.on_event(push_event_to_sse)
network_monitor.on_event(push_event_to_sse)
disk_monitor.on_event(push_event_to_sse)

set_monitor_service(monitor_service)
app.include_router(monitor_router)

# 8. Events routes (SSE)
from src.api.routes.events import router as events_router
app.include_router(events_router)

# Catch-all SPA at the end (§6.7)
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info("frontend_mounted", path=str(frontend_dist))
else:
    @app.get("/{full_path:path}")
    async def spa_catch_all(full_path: str):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            {"status": "ok", "app": "TikDown"},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    logger.info("frontend_dist_not_found_api_only_mode", path=str(frontend_dist))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )

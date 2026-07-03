import json
import os
import subprocess
import tempfile
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.auth import SessionDep, check_needs_setup
from src.db.models.admin import Admin
from src.db.models.monitored_account import MonitoredAccount
from src.db.models.setting import AppSetting
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.system")

# Public router for health (no auth)
public_router = APIRouter(prefix="/api/system", tags=["system"])
# Private router for everything else
router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[SessionDep])

_log_buffer: list[dict] = []
_MAX_LOG_BUFFER = settings.LOG_BUFFER_SIZE


def write_log_to_buffer(event: dict) -> None:
    global _log_buffer
    _log_buffer.append(event)
    if len(_log_buffer) > _MAX_LOG_BUFFER:
        _log_buffer = _log_buffer[-_MAX_LOG_BUFFER:]


@public_router.get("/health")
async def system_health(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    needs = await check_needs_setup(db)
    disk = {"free_gb": 0, "total_gb": 0}
    try:
        videos_dir = Path(settings.VIDEOS_DIR)
        videos_dir.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(videos_dir)
        disk["free_gb"] = round(usage.free / (1024 ** 3), 1)
        disk["total_gb"] = round(usage.total / (1024 ** 3), 1)
    except Exception:
        pass

    yt_dlp_version = "unknown"
    try:
        from yt_dlp import version as yt_version
        yt_dlp_version = yt_version.__version__
    except (ImportError, AttributeError):
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"], capture_output=True, text=True, timeout=5
            )
            yt_dlp_version = result.stdout.strip()
        except Exception:
            pass

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "disk_free_gb": disk["free_gb"],
        "yt_dlp_version": yt_dlp_version,
        "monitor": "stopped",
        "network_status": "online",
        "accounts": 0,
        "needs_setup": needs,
    }


@router.get("/metrics")
async def system_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(MonitoredAccount))
    accounts = result.scalars().all()
    total_accounts = len(accounts)
    ok_count = sum(1 for a in accounts if a.status == "ok")
    needs_review = sum(1 for a in accounts if a.status == "needs_review")
    paused = sum(1 for a in accounts if a.status == "paused")

    disk_info = {}
    try:
        usage = shutil.disk_usage(Path(settings.VIDEOS_DIR))
        disk_info = {
            "free_gb": round(usage.free / (1024 ** 3), 1),
            "total_gb": round(usage.total / (1024 ** 3), 1),
            "percent_used": round((usage.used / usage.total) * 100, 1),
        }
    except Exception:
        pass

    yt_dlp_version = "unknown"
    try:
        from yt_dlp import version as yt_version
        yt_dlp_version = yt_version.__version__
    except (ImportError, AttributeError):
        pass

    return {
        "accounts": {
            "total": total_accounts,
            "ok": ok_count,
            "needs_review": needs_review,
            "paused": paused,
        },
        "disk": disk_info,
        "yt_dlp_version": yt_dlp_version,
        "monitor": "stopped",
    }


@router.get("/logs")
async def system_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: str | None = Query(None),
) -> list[dict]:
    logs = list(_log_buffer)
    if level:
        logs = [log for log in logs if log.get("level", "").upper() == level.upper()]
    return logs[-limit:]


@router.get("/logs/stream")
async def system_logs_stream(request: Request) -> StreamingResponse:
    async def _generate():
        last_index = len(_log_buffer)
        while True:
            if await request.is_disconnected():
                break
            if len(_log_buffer) > last_index:
                for entry in _log_buffer[last_index:]:
                    yield f"data: {json.dumps(entry)}\n\n"
                last_index = len(_log_buffer)
            await asyncio.sleep(0.5)

    import asyncio
    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/about")
async def system_about() -> dict:
    yt_dlp_version = "unknown"
    try:
        from yt_dlp import version as yt_version
        yt_dlp_version = yt_version.__version__
    except (ImportError, AttributeError):
        pass

    import importlib.metadata
    try:
        app_version = importlib.metadata.version("tikdown")
    except importlib.metadata.PackageNotFoundError:
        app_version = "0.1.0"

    return {
        "app": "TikDown",
        "version": app_version,
        "yt_dlp_version": yt_dlp_version,
        "python_version": os.sys.version,
        "stack": "FastAPI + SQLAlchemy + APScheduler",
    }


@router.get("/export")
async def system_export(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(MonitoredAccount))
    accounts = result.scalars().all()

    settings_result = await db.execute(select(AppSetting))
    app_settings = settings_result.scalars().all()

    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "version": "1.0",
        "accounts": [
            {
                "tiktok_username": a.tiktok_username,
                "enabled": a.enabled,
                "status": a.status,
                "capture_mode": a.capture_mode,
            }
            for a in accounts
        ],
        "settings": {s.key: s.value for s in app_settings},
    }


@router.post("/import")
async def system_import(
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict:
    raw = await file.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    imported_count = 0
    for acc_data in data.get("accounts", []):
        username = acc_data.get("tiktok_username")
        if not username:
            continue
        existing = await db.execute(
            select(MonitoredAccount).where(MonitoredAccount.tiktok_username == username)
        )
        if existing.scalar_one_or_none():
            continue
        account = MonitoredAccount(
            tiktok_username=username,
            enabled=acc_data.get("enabled", True),
            status=acc_data.get("status", "ok"),
            capture_mode=acc_data.get("capture_mode", "history_and_monitor"),
        )
        db.add(account)
        imported_count += 1

    for key, value in data.get("settings", {}).items():
        existing = await db.get(AppSetting, key)
        if existing:
            existing.value = value
        else:
            db.add(AppSetting(key=key, value=value))

    await db.commit()
    logger.info("config_imported", accounts=imported_count)
    return {"message": "Configuration imported", "accounts_imported": imported_count}


@router.get("/backup")
async def system_backup(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    backup_dir = Path(settings.BACKUPS_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(UTC).strftime("%Y%m%d")
    backup_path = backup_dir / f"tikdown_{date_str}.db"

    db_path = Path(settings.DATABASE_PATH)
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    await db.execute(text(f"VACUUM INTO '{backup_path}'"))

    return FileResponse(
        str(backup_path),
        media_type="application/octet-stream",
        filename=f"tikdown_{date_str}.db",
    )

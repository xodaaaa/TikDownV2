from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import SessionDep, check_needs_setup
from src.db.models.cookie import Cookie
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.monitor")

router = APIRouter(prefix="/api/monitor", tags=["monitor"], dependencies=[SessionDep])

# Global references set from main.py
_monitor_service = None


def set_monitor_service(service) -> None:
    global _monitor_service
    _monitor_service = service


@router.get("/status")
async def monitor_status(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    if _monitor_service is None:
        return {"running": False, "error": "Monitor service not initialized"}
    return await _monitor_service.get_status()


@router.post("/start")
async def monitor_start(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    if _monitor_service is None:
        raise HTTPException(status_code=503, detail="Monitor service not initialized")

    needs = await check_needs_setup(db)
    if needs:
        raise HTTPException(
            status_code=403,
            detail={"needs_setup": True, "message": "Configure admin password first"},
        )

    result = await db.execute(
        select(Cookie).where(Cookie.status == "valid").limit(1)
    )
    has_valid_cookie = result.scalar_one_or_none() is not None
    if not has_valid_cookie:
        raise HTTPException(
            status_code=403,
            detail={"needs_cookie": True, "message": "Upload a valid cookie first"},
        )

    await _monitor_service.start()
    logger.info("monitor_started_via_api")
    return {"message": "Monitor started", "running": True}


@router.post("/stop")
async def monitor_stop() -> dict:
    if _monitor_service is None:
        raise HTTPException(status_code=503, detail="Monitor service not initialized")
    await _monitor_service.stop()
    logger.info("monitor_stopped_via_api")
    return {"message": "Monitor stopped", "running": False}

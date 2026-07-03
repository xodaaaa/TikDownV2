import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.auth import SessionDep
from src.db.models.monitored_account import MonitoredAccount
from src.db.models.video import Video
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.accounts")

router = APIRouter(prefix="/api/accounts", tags=["accounts"], dependencies=[SessionDep])


class AccountCreate(BaseModel):
    tiktok_username: str
    capture_mode: str = "history_and_monitor"


class AccountUpdate(BaseModel):
    enabled: bool | None = None
    status: str | None = None


class AccountResponse(BaseModel):
    id: str
    tiktok_username: str
    enabled: bool
    status: str
    capture_mode: str
    last_check_at: str | None = None
    last_video_timestamp: int | None = None
    consecutive_failures: int = 0
    avatar_url: str | None = None
    follower_count: int | None = None
    following_count: int | None = None
    total_likes: int | None = None
    video_count: int | None = None
    profile_last_refreshed: str | None = None
    backfill_status: str = "idle"
    backfill_cursor: str | None = None
    backfill_total: int | None = None
    backfill_done: int = 0
    created_at: str | None = None


def _account_to_response(acc: MonitoredAccount) -> AccountResponse:
    return AccountResponse(
        id=acc.id,
        tiktok_username=acc.tiktok_username,
        enabled=acc.enabled,
        status=acc.status,
        capture_mode=acc.capture_mode,
        last_check_at=acc.last_check_at.isoformat() if acc.last_check_at else None,
        last_video_timestamp=acc.last_video_timestamp,
        consecutive_failures=acc.consecutive_failures,
        avatar_url=acc.avatar_url,
        follower_count=acc.follower_count,
        following_count=acc.following_count,
        total_likes=acc.total_likes,
        video_count=acc.video_count,
        profile_last_refreshed=acc.profile_last_refreshed.isoformat()
        if acc.profile_last_refreshed
        else None,
        backfill_status=acc.backfill_status,
        backfill_cursor=acc.backfill_cursor,
        backfill_total=acc.backfill_total,
        backfill_done=acc.backfill_done,
        created_at=acc.created_at.isoformat() if acc.created_at else None,
    )


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    enabled: bool | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> list[AccountResponse]:
    stmt = select(MonitoredAccount).order_by(MonitoredAccount.created_at.desc())
    if enabled is not None:
        stmt = stmt.where(MonitoredAccount.enabled == enabled)
    if status_filter:
        stmt = stmt.where(MonitoredAccount.status == status_filter)
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [_account_to_response(a) for a in accounts]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    body: AccountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    existing = await db.execute(
        select(MonitoredAccount).where(MonitoredAccount.tiktok_username == body.tiktok_username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Account @{body.tiktok_username} already exists",
        )
    acc = MonitoredAccount(
        tiktok_username=body.tiktok_username,
        capture_mode=body.capture_mode,
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    logger.info("account_created", username=body.tiktok_username)
    return _account_to_response(acc)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return _account_to_response(acc)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    body: AccountUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if body.enabled is not None:
        acc.enabled = body.enabled
    if body.status is not None:
        acc.status = body.status
    await db.commit()
    await db.refresh(acc)
    logger.info("account_updated", username=acc.tiktok_username)
    return _account_to_response(acc)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await db.execute(
        select(Video).where(Video.monitored_account_id == account_id)
    )
    videos = result.scalars().all()
    videos_dir = Path(settings.VIDEOS_DIR)
    for v in videos:
        if v.file_path:
            fp = Path(v.file_path)
            if fp.exists():
                fp.unlink(missing_ok=True)
        if v.thumbnail_path:
            tp = Path(v.thumbnail_path)
            if tp.exists():
                tp.unlink(missing_ok=True)

    await db.delete(acc)
    await db.commit()
    logger.info("account_deleted", username=acc.tiktok_username)


@router.post("/{account_id}/check", response_model=dict)
async def check_account(
    account_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": f"Check queued for @{acc.tiktok_username}", "account_id": account_id}


@router.post("/{account_id}/backfill", response_model=dict)
async def start_backfill(
    account_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if acc.backfill_status == "backfilling":
        raise HTTPException(status_code=409, detail="Backfill already in progress")
    acc.backfill_status = "backfilling"
    await db.commit()
    logger.info("backfill_started", username=acc.tiktok_username)
    return {"message": f"Backfill started for @{acc.tiktok_username}", "account_id": account_id}


@router.post("/{account_id}/backfill/cancel", response_model=dict)
async def cancel_backfill(
    account_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if acc.backfill_status not in ("backfilling", "paused"):
        raise HTTPException(status_code=409, detail="No active backfill to cancel")
    acc.backfill_status = "cancelled"
    await db.commit()
    logger.info("backfill_cancelled", username=acc.tiktok_username)
    return {"message": f"Backfill cancelled for @{acc.tiktok_username}", "account_id": account_id}


@router.get("/{account_id}/avatar")
async def serve_avatar(
    account_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    acc = await db.get(MonitoredAccount, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if not acc.avatar_local_path:
        raise HTTPException(status_code=404, detail="No avatar available")
    avatar_path = Path(acc.avatar_local_path)
    if not avatar_path.exists():
        raise HTTPException(status_code=404, detail="Avatar file not found")
    from fastapi.responses import FileResponse
    return FileResponse(str(avatar_path))

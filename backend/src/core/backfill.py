from __future__ import annotations

import asyncio
import random
from typing import Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.integrity import IntegrityChecker
from src.db.models.monitored_account import MonitoredAccount
from src.db.models.video import Video

logger = structlog.get_logger("tikdown.backfill")

BACKFILL_DELAY_MIN = settings.BACKFILL_DELAY_MIN
BACKFILL_DELAY_MAX = settings.BACKFILL_DELAY_MAX
BACKFILL_PAUSE_EVERY_N = settings.BACKFILL_PAUSE_EVERY_N
BACKFILL_LONG_PAUSE_MIN = settings.BACKFILL_LONG_PAUSE_MIN
BACKFILL_LONG_PAUSE_MAX = settings.BACKFILL_LONG_PAUSE_MAX


class BackfillOrchestrator:
    def __init__(self, session_factory: Any):
        self._session_factory = session_factory
        self._running: dict[str, asyncio.Task] = {}
        self._cancel_signals: dict[str, asyncio.Event] = {}
        self._progress: dict[str, dict] = {}

    async def start_backfill(self, account_id: str) -> None:
        if account_id in self._running and not self._running[account_id].done():
            logger.warning("backfill already running", account_id=account_id)
            return

        cancel_event = asyncio.Event()
        self._cancel_signals[account_id] = cancel_event
        self._progress[account_id] = {"done": 0, "total": 0, "status": "starting"}

        task = asyncio.create_task(self._run_backfill(account_id, cancel_event))
        self._running[account_id] = task

    async def cancel_backfill(self, account_id: str) -> None:
        if account_id in self._cancel_signals:
            self._cancel_signals[account_id].set()
        if account_id in self._running and not self._running[account_id].done():
            self._running[account_id].cancel()
        async with self._session_factory() as session:
            await session.execute(
                update(MonitoredAccount)
                .where(MonitoredAccount.id == account_id)
                .values(backfill_status="cancelled")
            )
            await session.commit()
        self._progress[account_id] = {
            "done": self._progress.get(account_id, {}).get("done", 0),
            "total": self._progress.get(account_id, {}).get("total", 0),
            "status": "cancelled",
        }
        logger.info("backfill cancelled", account_id=account_id)

    def get_progress(self, account_id: str) -> dict:
        return self._progress.get(
            account_id, {"done": 0, "total": 0, "status": "idle"}
        )

    async def _emit_event(self, event_type: str, payload: dict) -> None:
        from src.db.models.event import Event

        async with self._session_factory() as session:
            session.add(Event(type=event_type, payload=payload))
            await session.commit()

    async def _run_backfill(
        self, account_id: str, cancel_event: asyncio.Event
    ) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MonitoredAccount).where(MonitoredAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            if not account:
                logger.error("account not found", account_id=account_id)
                return

            account.backfill_status = "backfilling"
            await session.commit()

        total = self._progress[account_id].get("total", 0)
        await self._emit_event(
            "backfill.started",
            {"username": account.tiktok_username, "total": total},
        )

        done = 0
        try:
            # Integrity check before resuming
            async with self._session_factory() as session:
                integrity_ok = await IntegrityChecker.check_last_video(
                    account_id, session
                )
                if not integrity_ok:
                    logger.warning(
                        "integrity check failed, will re-download last video",
                        account_id=account_id,
                    )

            # Simulate scanning and downloading videos in chronological order
            # In production this calls the DownloadEngine
            videos_to_process = self._progress[account_id].get("total", 100)
            for i in range(videos_to_process):
                if cancel_event.is_set():
                    await self._emit_event(
                        "backfill.interrupted",
                        {
                            "username": account.tiktok_username,
                            "lastCursor": account.backfill_cursor or "",
                        },
                    )
                    return

                await asyncio.sleep(
                    random.uniform(BACKFILL_DELAY_MIN, BACKFILL_DELAY_MAX)
                )

                done += 1
                self._progress[account_id] = {
                    "done": done,
                    "total": total,
                    "status": "backfilling",
                }

                await self._emit_event(
                    "backfill.progress",
                    {
                        "username": account.tiktok_username,
                        "done": done,
                        "total": total,
                    },
                )

                if i > 0 and i % BACKFILL_PAUSE_EVERY_N == 0:
                    long_pause = random.uniform(
                        BACKFILL_LONG_PAUSE_MIN, BACKFILL_LONG_PAUSE_MAX
                    )
                    logger.info(
                        "backfill long pause",
                        account_id=account_id,
                        pause_seconds=long_pause,
                    )
                    await asyncio.sleep(long_pause)

            async with self._session_factory() as session:
                await session.execute(
                    update(MonitoredAccount)
                    .where(MonitoredAccount.id == account_id)
                    .values(
                        backfill_status="completed",
                        backfill_done=done,
                    )
                )
                await session.commit()

            self._progress[account_id] = {
                "done": done,
                "total": total,
                "status": "completed",
            }
            await self._emit_event(
                "backfill.completed",
                {"username": account.tiktok_username, "downloaded": done},
            )
            logger.info("backfill completed", account_id=account_id, downloaded=done)

        except asyncio.CancelledError:
            await self._emit_event(
                "backfill.interrupted",
                {
                    "username": account.tiktok_username,
                    "lastCursor": account.backfill_cursor or "",
                },
            )
            raise
        except Exception as e:
            logger.error("backfill failed", account_id=account_id, error=str(e))
            async with self._session_factory() as session:
                await session.execute(
                    update(MonitoredAccount)
                    .where(MonitoredAccount.id == account_id)
                    .values(backfill_status="paused")
                )
                await session.commit()
            await self._emit_event(
                "backfill.paused",
                {
                    "username": account.tiktok_username,
                    "reason": f"Error: {e}",
                },
            )
        finally:
            self._running.pop(account_id, None)
            self._cancel_signals.pop(account_id, None)

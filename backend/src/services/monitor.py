import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.circuit_breaker import CircuitBreaker
from src.core.download_engine import DownloadEngine, ErrorKind
from src.core.disk_monitor import DiskMonitor
from src.core.network_monitor import NetworkMonitor
from src.core.task_queue import APSchedulerQueue
from src.db.models.monitored_account import MonitoredAccount
from src.db.session import async_session_factory
from src.services.cookies import CookiesService

logger = structlog.get_logger("tikdown.services.monitor")


class MonitorService:
    def __init__(
        self,
        download_engine: DownloadEngine | None = None,
        task_queue: APSchedulerQueue | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        network_monitor: NetworkMonitor | None = None,
        disk_monitor: DiskMonitor | None = None,
    ) -> None:
        self._running = False
        self._iteration = 0
        self._engine = download_engine or DownloadEngine()
        self._task_queue = task_queue or APSchedulerQueue()
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._network_monitor = network_monitor or NetworkMonitor()
        self._disk_monitor = disk_monitor or DiskMonitor()
        self._task: asyncio.Task | None = None
        self._event_callbacks: list = []

    def on_event(self, callback) -> None:
        self._event_callbacks.append(callback)
        self._network_monitor.on_event(callback)
        self._disk_monitor.on_event(callback)

    async def _emit_event(self, event_type: str, payload: dict) -> None:
        for cb in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event_type, payload)
                else:
                    cb(event_type, payload)
            except Exception:
                logger.exception("monitor_event_callback_failed")

    async def get_status(self) -> dict[str, Any]:
        queue_status = self._task_queue.get_status() if self._task_queue else {}
        return {
            "running": self._running,
            "iteration": self._iteration,
            "paused": queue_status.get("paused", False),
            "active_downloads": queue_status.get("active_count", 0),
            "queued_tasks": queue_status.get("queued", 0),
            "network_offline": self._network_monitor.is_offline if self._network_monitor else False,
        }

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_cycle())
        await self._network_monitor.start()
        await self._disk_monitor.start()
        logger.info("monitor_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._network_monitor.stop()
        await self._disk_monitor.stop()
        logger.info("monitor_stopped")

    async def _run_cycle(self) -> None:
        while self._running:
            try:
                self._iteration += 1
                await self._emit_event(
                    "monitor.cycle_started",
                    {"iteration": self._iteration, "accounts": []},
                )

                if self._network_monitor.is_offline:
                    logger.info("monitor_skipped_cycle_network_offline")
                    await asyncio.sleep(60)
                    continue

                async with async_session_factory() as db:
                    accounts = await self._get_active_accounts(db)

                    if not accounts:
                        logger.info("monitor_no_active_accounts")
                        await asyncio.sleep(30)
                        continue

                    for account in accounts:
                        if not self._running:
                            break
                        await self._check_account(db, account)

                await asyncio.sleep(settings.MONITOR_INTERVAL_MINUTES * 60)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("monitor_cycle_error")
                await asyncio.sleep(60)

    async def _get_active_accounts(self, db: AsyncSession) -> list[MonitoredAccount]:
        result = await db.execute(
            select(MonitoredAccount).where(
                MonitoredAccount.enabled == True,
                MonitoredAccount.backfill_status.in_(["idle", "completed", "cancelled"]),
            )
        )
        return list(result.scalars().all())

    async def _check_account(
        self, db: AsyncSession, account: MonitoredAccount
    ) -> None:
        if self._circuit_breaker.is_open(account.id):
            logger.warning("circuit_breaker_open", username=account.tiktok_username)
            if account.status != "paused":
                account.status = "paused"
                await db.commit()
            return

        await self._emit_event(
            "monitor.account_check_started",
            {"username": account.tiktok_username},
        )

        cookies_service = CookiesService(db)
        valid_cookies = await cookies_service.get_valid_cookies()

        if not valid_cookies:
            logger.warning("no_valid_cookies", username=account.tiktok_username)
            return

        cookie_path = await cookies_service.write_cookie_to_temp(valid_cookies[0])

        import os

        try:
            videos = await self._engine.list_videos(
                account.tiktok_username, cookies_path=cookie_path
            )
            account.last_check_at = datetime.now(UTC)
            account.consecutive_failures = 0
            self._circuit_breaker.record_success(account.id)
            await db.commit()

            if videos:
                await self._emit_event(
                    "monitor.new_videos_found",
                    {"count": len(videos), "accountId": account.id},
                )
        except Exception as e:
            error_kind = self._engine._classify_error(e)
            account.consecutive_failures += 1
            if error_kind in (ErrorKind.AUTH, ErrorKind.RATE_LIMIT, ErrorKind.IP_BLOCK):
                self._circuit_breaker.record_failure(account.id)
            await db.commit()
            logger.error(
                "account_check_failed",
                username=account.tiktok_username,
                error_kind=error_kind.value,
            )
        finally:
            try:
                os.unlink(cookie_path)
            except OSError:
                pass

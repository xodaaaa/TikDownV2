import asyncio
import shutil
from pathlib import Path

import structlog

from src.config import settings

logger = structlog.get_logger("tikdown.disk_monitor")


class DiskMonitor:
    def __init__(self) -> None:
        self._event_callbacks: list = []
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_warning: bool = False

    def on_event(self, callback) -> None:
        self._event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, payload: dict) -> None:
        for cb in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event_type, payload)
                else:
                    cb(event_type, payload)
            except Exception:
                logger.exception("disk_monitor_event_callback_failed")

    def check_disk(self) -> dict:
        videos_dir = Path(settings.VIDEOS_DIR)
        videos_dir.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(videos_dir)
        total_gb = usage.total / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        percent_free = (usage.free / usage.total) * 100
        return {
            "total_gb": round(total_gb, 1),
            "free_gb": round(free_gb, 1),
            "percent_free": round(percent_free, 1),
            "percent_used": round(100 - percent_free, 1),
        }

    async def _run_cycle(self) -> None:
        while self._running:
            try:
                info = self.check_disk()
                if info["percent_free"] < 10 and not self._last_warning:
                    self._last_warning = True
                    await self._emit_event(
                        "monitor.disk_warning",
                        {
                            "free_gb": info["free_gb"],
                            "percent": info["percent_free"],
                        },
                    )
                    logger.warning("disk_space_low", **info)
                elif info["percent_free"] >= 10:
                    self._last_warning = False
            except Exception:
                logger.exception("disk_monitor_check_failed")
            await asyncio.sleep(settings.DISK_MONITOR_INTERVAL_SECONDS)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_cycle())
        logger.info("disk_monitor_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("disk_monitor_stopped")

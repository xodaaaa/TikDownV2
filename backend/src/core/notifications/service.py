from __future__ import annotations

import asyncio
from typing import Any

import structlog

from src.core.notifications.base import ActivityEvent, BaseNotifier, list_notifiers

logger = structlog.get_logger("tikdown.notification_service")

DEFAULT_DISPATCH_TIMEOUT = 10.0


class NotificationService:
    def __init__(self):
        self._notifiers: list[BaseNotifier] = []

    def register(self, notifier: BaseNotifier) -> None:
        self._notifiers.append(notifier)

    def register_from_settings(self) -> None:
        from src.config import settings

        if not settings.ENABLE_EXTERNAL_NOTIFICATIONS:
            return
        mode = settings.TELEGRAM_BOT_MODE
        if mode in ("notifications", "both"):
            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                from src.core.notifications.telegram import TelegramNotifier

                self.register(TelegramNotifier())
                logger.info("telegram notifier registered")

    async def dispatch(self, event: ActivityEvent) -> None:
        if not self._notifiers:
            return
        coros = [self._safe_send(n, event) for n in self._notifiers]
        await asyncio.gather(*coros, return_exceptions=True)

    async def _safe_send(
        self, notifier: BaseNotifier, event: ActivityEvent
    ) -> None:
        try:
            await asyncio.wait_for(
                notifier.send(event), timeout=DEFAULT_DISPATCH_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning("notification dispatch timed out", notifier=type(notifier).__name__)
        except Exception as e:
            logger.error(
                "notification dispatch failed",
                notifier=type(notifier).__name__,
                error=str(e),
            )

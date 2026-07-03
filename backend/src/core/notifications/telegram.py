from __future__ import annotations

import re
from typing import Any

import httpx
import structlog

from src.config import settings
from src.core.notifications.base import ActivityEvent, BaseNotifier, register_notifier

logger = structlog.get_logger("tikdown.telegram_notifier")

DEFAULT_EVENTS = {
    "monitor.new_videos_found",
    "monitor.cookie_expired",
    "monitor.cookie_expiring_soon",
    "monitor.account_paused",
    "monitor.yt_dlp_update_available",
    "monitor.disk_warning",
    "backfill.completed",
    "network.online",
}

OPT_IN_EVENTS = {
    "download.completed",
    "backfill.completed",
}


def escape_markdown_v2(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


class TelegramNotifier(BaseNotifier):
    def __init__(self):
        self._token = settings.TELEGRAM_BOT_TOKEN or ""
        self._chat_id = settings.TELEGRAM_CHAT_ID or ""
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10)
        return self._http_client

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "MarkdownV2",
    ) -> dict[str, Any] | None:
        if not self._token or not chat_id:
            logger.warning("telegram not configured")
            return None
        client = await self._get_client()
        try:
            resp = await client.post(
                f"https://api.telegram.org/bot{self._token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("telegram send failed", error=str(e))
            return None

    async def send(self, event: ActivityEvent) -> None:
        if not self._token or not self._chat_id:
            return
        if event.type not in DEFAULT_EVENTS and event.type not in OPT_IN_EVENTS:
            return
        text = self._format_event(event)
        if text:
            await self.send_message(self._chat_id, text)

    def _format_event(self, event: ActivityEvent) -> str | None:
        p = event.payload
        mappings = {
            "monitor.new_videos_found": (
                lambda: f"*Nuevos vídeos:* {p.get('count', 0)} encontrados"
            ),
            "monitor.cookie_expired": (lambda: "*Cookie expirada* — re-importa las cookies"),
            "monitor.cookie_expiring_soon": (
                lambda: f"*Cookie expira pronto:* {p.get('daysLeft', '?')} días restantes"
            ),
            "monitor.account_paused": (
                lambda: f"*Cuenta pausada:* {p.get('username', '?')} — {p.get('reason', '')}"
            ),
            "monitor.yt_dlp_update_available": (
                lambda: f"*yt-dlp actualizable:* {p.get('currentVersion', '?')} → {p.get('latestVersion', '?')}"
            ),
            "monitor.disk_warning": (
                lambda: f"*Disco bajo:* {p.get('freeGB', 0):.1f} GB libre ({p.get('percent', 0)}%)"
            ),
            "download.completed": (
                lambda: f"*Descarga completada:* {p.get('title', '?')}"
            ),
            "backfill.completed": (
                lambda: f"*Backfill completado:* @{p.get('username', '?')} — {p.get('downloaded', 0)} vídeos"
            ),
            "network.online": (
                lambda: f"*Conexión restablecida* tras {p.get('durationHours', 0):.1f}h, {p.get('newVideosFound', 0)} vídeos nuevos"
            ),
        }
        formatter = mappings.get(event.type)
        if formatter:
            return escape_markdown_v2(formatter())
        return None


register_notifier("telegram", TelegramNotifier)

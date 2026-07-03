from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger("tikdown.telegram_bot")


class TelegramBotClient:
    def __init__(self, token: str):
        self._token = token
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15)
        return self._client

    async def get_updates(
        self, offset: int = 0, timeout: int = 30
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.post(
                f"{self._base_url}/getUpdates",
                json={"offset": offset, "timeout": timeout},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
            logger.error("getUpdates not ok", description=data.get("description"))
            return []
        except httpx.HTTPError as e:
            logger.error("getUpdates http error", error=str(e))
            return []

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "MarkdownV2",
        reply_markup: dict | None = None,
    ) -> dict[str, Any] | None:
        client = await self._get_client()
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            resp = await client.post(
                f"{self._base_url}/sendMessage",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("sendMessage error", error=str(e))
            return None

    async def answer_callback_query(
        self, callback_query_id: str
    ) -> dict[str, Any] | None:
        client = await self._get_client()
        try:
            resp = await client.post(
                f"{self._base_url}/answerCallbackQuery",
                json={"callback_query_id": callback_query_id},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("answerCallbackQuery error", error=str(e))
            return None

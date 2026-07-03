from __future__ import annotations

import time
from typing import Any

import structlog

from src.config import settings
from src.core.notifications.telegram_bot.bot import TelegramBotClient
from src.core.notifications.telegram_bot.commands import COMMANDS

logger = structlog.get_logger("tikdown.telegram_dispatcher")

THROTTLE_SECONDS = 2.0


class Dispatcher:
    def __init__(self, bot: TelegramBotClient):
        self._bot = bot
        self._authorized_chat_id = settings.TELEGRAM_CHAT_ID or ""
        self._last_command_time: dict[str, float] = {}
        self._confirmations: dict[str, float] = {}

    async def process_update(self, update: dict[str, Any]) -> None:
        if "message" in update:
            await self._handle_message(update["message"])
        elif "callback_query" in update:
            await self._handle_callback_query(update["callback_query"])

    async def _handle_message(self, message: dict[str, Any]) -> None:
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        if not self._is_authorized(chat_id):
            logger.warning(
                "unauthorized access attempt",
                chat_id=chat_id,
                username=message.get("from", {}).get("username"),
            )
            return

        if not text.startswith("/"):
            await self._bot.send_message(
                chat_id,
                "Envía /help para ver los comandos disponibles.",
            )
            return

        if not self._check_throttle(chat_id):
            await self._bot.send_message(
                chat_id, f"Espera {THROTTLE_SECONDS:.0f}s antes del próximo comando."
            )
            return

        parts = text.split(maxsplit=1)
        cmd = parts[0].lstrip("/").lower()
        args = parts[1] if len(parts) > 1 else ""

        logger.info(
            "command received",
            command=cmd,
            chat_id=chat_id,
            args=args,
        )

        handler = COMMANDS.get(cmd)
        if handler:
            try:
                await handler(self._bot, chat_id, args)
            except Exception as e:
                logger.error("command handler error", command=cmd, error=str(e))
                await self._bot.send_message(
                    chat_id, f"Error al ejecutar /{cmd}: {e}"
                )
        else:
            await self._bot.send_message(
                chat_id, f"Comando /{cmd} no reconocido. Usa /help para la lista."
            )

    async def _handle_callback_query(self, query: dict[str, Any]) -> None:
        callback_id = query.get("id", "")
        data = query.get("data", "")
        chat_id = str(query.get("message", {}).get("chat", {}).get("id", ""))

        if not self._is_authorized(chat_id):
            logger.warning(
                "unauthorized callback query",
                chat_id=chat_id,
                data=data,
            )
            await self._bot.answer_callback_query(callback_id)
            return

        logger.info("callback query received", data=data, chat_id=chat_id)

        parts = data.split(":")
        if len(parts) < 2:
            await self._bot.answer_callback_query(callback_id)
            return

        action, sub_action = parts[0], parts[1]
        target = parts[2] if len(parts) > 2 else ""

        if sub_action == "confirm":
            confirm_key = f"{action}:{target}"
            created = self._confirmations.get(confirm_key)
            if created and time.monotonic() - created > 60:
                await self._bot.send_message(
                    chat_id,
                    "Confirmación expirada (60s). Vuelve a lanzar el comando.",
                )
                await self._bot.answer_callback_query(callback_id)
                return

            if action == "delete":
                logger.info("action confirmed", action="delete", target=target)
                await self._bot.send_message(
                    chat_id, f"Cuenta @{target} borrada."
                )
            elif action == "monitor_stop":
                logger.info("action confirmed", action="monitor_stop")
                await self._bot.send_message(chat_id, "Monitor detenido.")

            self._confirmations.pop(confirm_key, None)

        elif sub_action == "cancel":
            await self._bot.send_message(chat_id, "Acción cancelada.")

        elif action == "list" and sub_action == "page":
            # In production would re-query from the DB
            await self._bot.send_message(
                chat_id, f"Página {target} (simulado)."
            )

        await self._bot.answer_callback_query(callback_id)

    def _is_authorized(self, chat_id: str) -> bool:
        return chat_id == self._authorized_chat_id

    def _check_throttle(self, chat_id: str) -> bool:
        now = time.monotonic()
        last = self._last_command_time.get(chat_id, 0.0)
        if now - last < THROTTLE_SECONDS:
            return False
        self._last_command_time[chat_id] = now
        return True

    def set_confirmation(self, key: str) -> None:
        self._confirmations[key] = time.monotonic()

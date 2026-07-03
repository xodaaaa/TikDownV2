from __future__ import annotations

from typing import Any

from src.core.notifications.telegram_bot.bot import TelegramBotClient
from src.core.notifications.telegram_bot.keyboards import (
    confirm_keyboard,
    pagination_keyboard,
)


async def cmd_start(bot: TelegramBotClient, chat_id: str, _args: str = "") -> None:
    text = (
        "*TikDown Bot* — Comandos disponibles:\n\n"
        "/start /help — Esta lista\n"
        "/list — Cuentas monitorizadas\n"
        "/add @usuario [history|monitor] — Añadir cuenta\n"
        "/stats @usuario — Estadísticas\n"
        "/disk — Espacio en disco\n"
        "/status — Estado del monitor\n"
        "/monitor start|stop — Iniciar/detener monitor\n"
        "/check @usuario — Check now\n"
        "/backfill @usuario — Lanzar backfill\n"
        "/pause @usuario — Pausar cuenta\n"
        "/enable @usuario — Reactivar cuenta\n"
        "/delete @usuario — Borrar cuenta\n"
        "/cookies — Estado de cookies\n"
        "/last [N] — Últimos N vídeos"
    )
    await bot.send_message(chat_id, text)


cmd_help = cmd_start


async def cmd_list(bot: TelegramBotClient, chat_id: str, _args: str = "") -> None:
    # Simulated list with pagination (in production queries the DB)
    import structlog

    logger = structlog.get_logger("tikdown.telegram_commands")
    logger.info("command executed", command="list", chat_id=chat_id)

    items = ["@usuario1 — ok (15 vídeos)", "@usuario2 — needs_review (3 vídeos)"]
    if not items:
        await bot.send_message(chat_id, "No hay cuentas monitorizadas.")
        return
    page = 0
    per_page = 8
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    start = page * per_page
    lines = items[start : start + per_page]
    text = "*Cuentas monitorizadas:*\n" + "\n".join(f"- {l}" for l in lines)
    kb = pagination_keyboard(page, total_pages)
    await bot.send_message(chat_id, text, reply_markup=kb)


async def cmd_add(bot: TelegramBotClient, chat_id: str, args: str = "") -> None:
    import structlog

    logger = structlog.get_logger("tikdown.telegram_commands")
    logger.info("command executed", command="add", chat_id=chat_id, args=args)

    parts = args.split()
    if not parts:
        await bot.send_message(chat_id, "Uso: /add @usuario [history|monitor]")
        return
    username = parts[0].lstrip("@")
    mode = parts[1] if len(parts) > 1 else "history"
    if mode not in ("history", "monitor"):
        await bot.send_message(chat_id, "Modo debe ser 'history' o 'monitor'")
        return
    await bot.send_message(
        chat_id, f"Cuenta @{username} añadida (modo: {mode}). El backfill comenzará en breve."
    )


async def cmd_stats(bot: TelegramBotClient, chat_id: str, args: str = "") -> None:
    if not args:
        await bot.send_message(chat_id, "Uso: /stats @usuario")
        return
    username = args.lstrip("@")
    await bot.send_message(
        chat_id,
        f"*Estadísticas @{username}:*\n"
        "Total: 100\nDescargados: 85\nFallidos: 2\nEn cola: 13\nÚltimo check: hace 5m",
    )


async def cmd_disk(bot: TelegramBotClient, chat_id: str, _args: str = "") -> None:
    import shutil

    usage = shutil.disk_usage(".")
    free_gb = usage.free / (1024**3)
    total_gb = usage.total / (1024**3)
    pct = usage.used / usage.total * 100
    await bot.send_message(
        chat_id,
        f"*Disco:* {free_gb:.1f} GB libres de {total_gb:.1f} GB ({pct:.0f}% usado)",
    )


async def cmd_status(bot: TelegramBotClient, chat_id: str, _args: str = "") -> None:
    await bot.send_message(
        chat_id,
        "*Estado del monitor:*\n"
        "Monitor: stopped\n"
        "Próxima iteración: —\n"
        "Cuentas activas: 2\n"
        "Descargas hoy: 5",
    )


async def cmd_monitor(
    bot: TelegramBotClient, chat_id: str, args: str = ""
) -> None:
    action = args.strip().lower()
    if action not in ("start", "stop"):
        await bot.send_message(chat_id, "Uso: /monitor start|stop")
        return
    if action == "start":
        await bot.send_message(chat_id, "Monitor iniciado.")
    elif action == "stop":
        kb = confirm_keyboard("monitor_stop", "global")
        await bot.send_message(
            chat_id, "¿Detener el monitor?", reply_markup=kb
        )


async def cmd_check(bot: TelegramBotClient, chat_id: str, args: str = "") -> None:
    if not args:
        await bot.send_message(chat_id, "Uso: /check @usuario")
        return
    username = args.lstrip("@")
    await bot.send_message(chat_id, f"Check Now lanzado para @{username}.")


async def cmd_backfill(
    bot: TelegramBotClient, chat_id: str, args: str = ""
) -> None:
    if not args:
        await bot.send_message(chat_id, "Uso: /backfill @usuario")
        return
    username = args.lstrip("@")
    await bot.send_message(chat_id, f"Backfill iniciado para @{username}.")


async def cmd_pause(bot: TelegramBotClient, chat_id: str, args: str = "") -> None:
    if not args:
        await bot.send_message(chat_id, "Uso: /pause @usuario")
        return
    username = args.lstrip("@")
    await bot.send_message(chat_id, f"Cuenta @{username} pausada.")


async def cmd_enable(bot: TelegramBotClient, chat_id: str, args: str = "") -> None:
    if not args:
        await bot.send_message(chat_id, "Uso: /enable @usuario")
        return
    username = args.lstrip("@")
    await bot.send_message(chat_id, f"Cuenta @{username} reactivada.")


async def cmd_delete(
    bot: TelegramBotClient, chat_id: str, args: str = ""
) -> None:
    if not args:
        await bot.send_message(chat_id, "Uso: /delete @usuario")
        return
    username = args.lstrip("@")
    kb = confirm_keyboard("delete", username)
    await bot.send_message(
        chat_id, f"¿Borrar cuenta @{username} y todos sus vídeos?", reply_markup=kb
    )


async def cmd_cookies(
    bot: TelegramBotClient, chat_id: str, _args: str = ""
) -> None:
    await bot.send_message(
        chat_id,
        "*Cookies:*\n"
        "1. cookies.txt — válida (5 días)\n"
        "2. cookies.json — expirada",
    )


async def cmd_last(bot: TelegramBotClient, chat_id: str, args: str = "") -> None:
    try:
        n = int(args.strip()) if args.strip() else 5
    except ValueError:
        n = 5
    if n < 1:
        n = 5
    if n > 20:
        n = 20
    lines = [
        f"{i}. Vídeo {i} — @usuario — 2026-07-03" for i in range(1, n + 1)
    ]
    await bot.send_message(chat_id, "*Últimos vídeos:*\n" + "\n".join(lines))


COMMANDS: dict[str, Any] = {
    "start": cmd_start,
    "help": cmd_help,
    "list": cmd_list,
    "add": cmd_add,
    "stats": cmd_stats,
    "disk": cmd_disk,
    "status": cmd_status,
    "monitor": cmd_monitor,
    "check": cmd_check,
    "backfill": cmd_backfill,
    "pause": cmd_pause,
    "enable": cmd_enable,
    "delete": cmd_delete,
    "cookies": cmd_cookies,
    "last": cmd_last,
}

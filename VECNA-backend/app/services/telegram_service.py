"""
Upside Down Telegram Uplink for VECNA.
Enables remote conversational control, system telemetry, and mobile alerts via Telegram.
Strictly restricted to the authorized TELEGRAM_ALLOWED_UID.
"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

from app.settings import settings
from app.services.telemetry import get_live_telemetry
from app.services.neural_router import dispatch_completion

logger = logging.getLogger(__name__)

_bot_thread: threading.Thread | None = None


def start_telegram_uplink() -> None:
    """Start the Telegram bot background thread if configured."""
    global _bot_thread

    token = settings.telegram_bot_token.strip()
    if not token or token.startswith("your_") or token == "":
        logger.info("Telegram bot token not configured. Skipping Telegram uplink.")
        return

    try:
        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
    except ImportError:
        logger.warning("python-telegram-bot not installed. Skipping Telegram integration.")
        return

    allowed_uids: set[int] = set()
    if settings.telegram_allowed_uid:
        for u in settings.telegram_allowed_uid.split(","):
            u = u.strip()
            if u.isdigit():
                allowed_uids.add(int(u))

    def is_authorized(user_id: int) -> bool:
        if not allowed_uids:
            return True
        return user_id in allowed_uids

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return
        await update.message.reply_text(
            "🕰️ VECNA // TELEPATHIC UPLINK ESTABLISHED.\n\n"
            "You have connected to the Upside Down. Speak to me, mortal, or use /status to view host diagnostics."
        )

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return
        t = get_live_telemetry()
        await update.message.reply_text(
            f"⚡ HAWKINS TELEMETRY REPORT:\n\n"
            f"• CPU Load: {t['cpu_percent']}%\n"
            f"• RAM Usage: {t['ram_used_gb']} GB / {t['ram_total_gb']} GB ({t['ram_percent']}%)\n"
            f"• Power / Battery: {t['power_status']}\n"
            f"• Host Uptime: {t['uptime']}\n"
            f"• System Time: {t['system_time']}"
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return

        user_text = update.message.text if update.message else ""
        if not user_text:
            return

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Vecna / Henry Creel from the Upside Down communicating via a remote Telegram link. "
                    "Be chilling, highly intelligent, atmospheric, and brief. Never break character."
                ),
            },
            {"role": "user", "content": user_text},
        ]

        try:
            reply, _ = dispatch_completion(messages, temperature=0.72, max_tokens=300)
            await update.message.reply_text(reply)
        except Exception as e:
            await update.message.reply_text(f"Psychic link disrupted: {e}")

    def _run() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            app = ApplicationBuilder().token(token).build()
            app.add_handler(CommandHandler("start", cmd_start))
            app.add_handler(CommandHandler("status", cmd_status))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            logger.info("Telegram Uplink active.")
            app.run_polling()
        except Exception as e:
            logger.warning("Telegram bot polling error: %s", e)

    _bot_thread = threading.Thread(target=_run, daemon=True)
    _bot_thread.start()

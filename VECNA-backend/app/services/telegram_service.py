"""
Upside Down Telegram Uplink for VECNA.
Enables remote conversational control, system telemetry, and mobile alerts via Telegram.
Strictly restricted to the authorized TELEGRAM_ALLOWED_UID.

Thread-safe implementation using python-telegram-bot v20+ lifecycle API
(initialize/start/updater.start_polling) instead of run_polling() to prevent
event loop conflicts when running alongside FastAPI/uvicorn.
"""
from __future__ import annotations

import asyncio
import logging
import re
import threading

from app.settings import settings
from app.services.telemetry import get_live_telemetry
from app.services.neural_router import dispatch_completion

logger = logging.getLogger(__name__)

_bot_thread: threading.Thread | None = None
_shutdown_event: threading.Event = threading.Event()


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

    # Parse allowed user IDs
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
            "VECNA // TELEPATHIC UPLINK ESTABLISHED.\n\n"
            "You have connected to the Upside Down. Speak to me, mortal, "
            "or use /status to view host diagnostics.\n\n"
            "Commands:\n"
            "/start — establish uplink\n"
            "/status — host telemetry report\n"
            "/help — show commands"
        )

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return
        await update.message.reply_text(
            "VECNA COMMAND UPLINK:\n\n"
            "/start — establish telepathic connection\n"
            "/status — live host diagnostics\n"
            "/help — show this menu\n\n"
            "Or simply type any message to speak directly with Vecna."
        )

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return
        t = get_live_telemetry()
        await update.message.reply_text(
            "HAWKINS TELEMETRY REPORT:\n\n"
            f"CPU Load:    {t['cpu_percent']}%\n"
            f"RAM Usage:   {t['ram_used_gb']} GB / {t['ram_total_gb']} GB ({t['ram_percent']}%)\n"
            f"Disk Free:   {t['disk_free_gb']} GB ({t['disk_percent']}% used)\n"
            f"Power:       {t['power_status']}\n"
            f"Uptime:      {t['uptime']}\n"
            f"System Time: {t['system_time']}, {t['system_date']}"
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not is_authorized(update.effective_user.id):
            await update.message.reply_text("Unauthorized. The Upside Down does not answer to you.")
            return

        user_text = update.message.text if update.message else ""
        if not user_text or not user_text.strip():
            return

        # Show typing indicator while generating reply
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing",
        )

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are Vecna / Henry Creel from the Upside Down communicating via Telegram. "
                    "Be chilling, highly intelligent, atmospheric, and concise — 2-3 sentences max. "
                    "Never use markdown formatting (no **bold**, no *italic*, no bullet lists). "
                    "Never break character. Do not use emojis."
                ),
            },
            {"role": "user", "content": user_text.strip()},
        ]

        try:
            reply, _ = await asyncio.to_thread(
                dispatch_completion, messages, 0.72, 300
            )
            # Strip any markdown that leaked through
            reply = re.sub(r"\*\*(.+?)\*\*", r"\1", reply)
            reply = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", reply)
            await update.message.reply_text(reply)
        except Exception as e:
            logger.warning("Telegram message handler error: %s", e)
            await update.message.reply_text(
                "The psychic link was disrupted. Try again."
            )

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors but keep the bot running."""
        logger.warning("Telegram update caused error: %s", context.error)

    def _run() -> None:
        """Run the Telegram bot in a fresh isolated event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _bot_main() -> None:
            from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
            app = ApplicationBuilder().token(token).build()
            app.add_handler(CommandHandler("start", cmd_start))
            app.add_handler(CommandHandler("help", cmd_help))
            app.add_handler(CommandHandler("status", cmd_status))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            app.add_error_handler(error_handler)

            logger.info("Telegram Uplink: Initializing @VECNA_AIBOT...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message"],
            )
            logger.info("Telegram Uplink: @VECNA_AIBOT is live and polling.")

            # Keep alive until shutdown signal
            while not _shutdown_event.is_set():
                await asyncio.sleep(1.0)

            # Graceful shutdown
            logger.info("Telegram Uplink: Shutting down...")
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            logger.info("Telegram Uplink: Shutdown complete.")

        try:
            loop.run_until_complete(_bot_main())
        except Exception as e:
            logger.warning("Telegram bot fatal error: %s", e)
        finally:
            try:
                loop.close()
            except Exception:
                pass

    _shutdown_event.clear()
    _bot_thread = threading.Thread(target=_run, daemon=True, name="vecna-telegram-uplink")
    _bot_thread.start()
    logger.info("Telegram Uplink thread started (python-telegram-bot v%s).", __import__("telegram").__version__)

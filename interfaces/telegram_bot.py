import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("RPG_BOT_TOKEN", "")
WEB_HOST = os.environ.get("WEB_HOST", "127.0.0.1")
WEB_PORT = os.environ.get("WEB_PORT", "8080")
ADMIN_IDS_STR = os.environ.get("TELEGRAM_ADMIN_IDS", "")
ADMIN_IDS = set(ADMIN_IDS_STR.split(",")) if ADMIN_IDS_STR else set()


def _is_authorized(update: Update) -> bool:
    if not ADMIN_IDS:
        return True
    return str(update.effective_user.id) in ADMIN_IDS


def _is_https_url(url: str) -> bool:
    return url.startswith("https://")


class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self._register_handlers()

    def _register_handlers(self):
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            if not user:
                return
            if not _is_authorized(update):
                await update.message.reply_text("Access denied.")
                return

            web_url = f"http://{WEB_HOST}:{WEB_PORT}"

            if _is_https_url(web_url):
                # Production: Mini App button
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "Open XUMOTION Console",
                        web_app=WebAppInfo(url=web_url)
                    )]
                ])
                await update.message.reply_text(
                    "⚡ XUMOTION — Systems Console\n\n"
                    "Tap to open the dashboard.",
                    reply_markup=keyboard
                )
            else:
                # Development: text-only with link
                await update.message.reply_text(
                    "⚡ XUMOTION — Systems Console\n\n"
                    f"Dashboard: {web_url}\n\n"
                    "Open in browser to play.\n"
                    "Commands: /start, /help"
                )

        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "Use the web dashboard for full interaction.\n"
                "Commands: /start, /help"
            )

        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(CommandHandler("help", help_cmd))

    async def run(self):
        if not TELEGRAM_TOKEN:
            print("TELEGRAM_BOT_TOKEN not set. Bot not started.")
            return
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        print("Telegram bot started (Mini App mode).")
        while True:
            await asyncio.sleep(1)

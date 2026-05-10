import asyncio
import threading
from dotenv import load_dotenv
load_dotenv()
from game.database import init_db
init_db()

from web.server import start_web
from interfaces.telegram_bot import TelegramBot


def main():
    # Start web dashboard (HTTP + WebSocket)
    start_web()

    # Start Telegram bot (Mini App mode)
    bot = TelegramBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Shutting down.")


if __name__ == "__main__":
    main()

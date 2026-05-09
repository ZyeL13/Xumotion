import asyncio
import threading
from dotenv import load_dotenv
load_dotenv()
from game.database import init_db
init_db()

# ruff: noqa: E402
from game.state import GameState
from game.save_manager import load_game
from game.engine import game_loop
from models.player import Player
from models.enemy import Enemy
from interfaces.telegram_bot import TelegramBot
from game.offline import calculate_offline_reward
from systems.daily import can_claim
from web.server import start_web


def main():
    state = load_game()
    if state is None:
        state = GameState(
            player=Player(),
            enemy=Enemy.generate(sector=1, substage=1, player=Player()),
            offline_message="SYSTEMS ONLINE.",
        )
    else:
        calculate_offline_reward(state)

    if can_claim():
        state.offline_message += " | Cycle deposit available. /cycle"

    # Start web dashboard
    start_web(state)

    # Start game loop in background thread
    game_thread = threading.Thread(target=game_loop, args=(state,), daemon=True)
    game_thread.start()

    # Start Telegram bot in main async event loop
    bot = TelegramBot(state)
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Interrupted. Shutting down.")

if __name__ == "__main__":
    main()

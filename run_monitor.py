import threading
from game.state import GameState
from game.save_manager import load_game
from game.engine import game_loop
from models.player import Player
from models.enemy import Enemy
from game.offline import calculate_offline_reward
from interfaces.cli_monitor import monitor_loop

if __name__ == "__main__":
    state = load_game()
    if not state:
        state = GameState(
            player=Player(),
            enemy=Enemy.generate(stage=1),
        )
    else:
        calculate_offline_reward(state)

    game_thread = threading.Thread(target=game_loop, args=(state,), daemon=True)
    game_thread.start()

    monitor_loop(state)

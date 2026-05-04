import json
import os
import time
from models.player import Player
from models.enemy import Enemy
from game.state import GameState

SAVE_PATH = "saves/savegame.json"
CURRENT_VERSION = 1


def save_game(state: GameState):
    data = {
        "version": CURRENT_VERSION,
        "player": state.player.to_dict(),
        "current_stage": state.current_stage,
        "kills_in_stage": state.kills_in_stage,
        "last_save": time.time(),
    }
    if state.enemy:
        data["enemy"] = state.enemy.to_dict()
    else:
        data["enemy"] = None

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def load_game() -> GameState | None:
    if not os.path.exists(SAVE_PATH):
        return None

    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    if not data or "player" not in data:
        return None

    version = data.get("version", 0)
    # Migration jika diperlukan (placeholder)
    if version < CURRENT_VERSION:
        _migrate(data, version)

    player = Player.from_dict(data["player"])
    enemy_data = data.get("enemy")
    enemy = Enemy.from_dict(enemy_data) if enemy_data else Enemy.generate(data.get("current_stage", 1))

    state = GameState(
        player=player,
        enemy=enemy,
        current_stage=data.get("current_stage", 1),
        kills_in_stage=data.get("kills_in_stage", 0),
        last_save=data.get("last_save", time.time()),
    )
    return state


def _migrate(data: dict, from_version: int):
    # Contoh migrasi di masa depan:
    # if from_version < 2:
    #     # tambah field baru
    #     data["player"]["new_field"] = default_value
    pass

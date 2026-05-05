import json
import os
import time
from models.player import Player
from game.state import GameState

def _validate_player_save(data: dict) -> bool:
    """Validate save data against hard limits based on current stage."""
    player = data.get("player", {})
    stage = max(1, data.get("current_stage", 1))
    
    # Hard limits
    max_gold = int(stage * 1000 * (1.2 ** stage)) + 100000
    max_level = stage // 5 + 50
    max_upgrades = stage * 2 + 100
    max_core = stage * 10 + 50
    max_inventory = stage * 5 + 100
    max_agents = stage * 3 + 50
    
    if player.get("gold", 0) > max_gold:
        raise ValueError(f"Gold {player['gold']} exceeds stage {stage} limit {max_gold}")
    if player.get("level", 0) > max_level:
        raise ValueError(f"Level {player['level']} exceeds stage {stage} limit {max_level}")
    for key in ["atk_upgrade_lvl", "def_upgrade_lvl", "hp_upgrade_lvl", "crit_upgrade_lvl"]:
        if player.get(key, 0) > max_upgrades:
            raise ValueError(f"{key} {player[key]} exceeds limit {max_upgrades}")
    if player.get("core_points", 0) > max_core:
        raise ValueError(f"Core points {player['core_points']} exceeds limit {max_core}")
    if len(player.get("inventory", [])) > max_inventory:
        raise ValueError(f"Inventory size exceeds limit {max_inventory}")
    if len(player.get("agents", [])) > max_agents:
        raise ValueError(f"Agent count exceeds limit {max_agents}")
    
    return True

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
    from models.enemy import Enemy  # late import to avoid circular dependency

    if not os.path.exists(SAVE_PATH):
        return None

    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
        _validate_player_save(data)
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
        # Secara opsional log error, tapi kita tidak punya logger global.
        # Cukup kembalikan None agar memulai game baru.
        return None

    if not data or "player" not in data:
        return None

    version = data.get("version", 0)
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
    pass

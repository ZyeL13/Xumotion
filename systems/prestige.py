"""
Recompile system - reset progress for permanent core bonuses.
"""
from models.player import Player
from models.enemy import Enemy
from game.constants import PRESTIGE_STAGE_REQ, CORE_PER_STAGE
from game.event_logger import event_logger


def can_prestige(state) -> bool:
    # Cek apakah sudah mencapai sektor minimum untuk recompile
    return state.sector >= PRESTIGE_STAGE_REQ


def get_core_gain(state) -> int:
    # Gunakan stage ekivalen untuk menghitung core gain (agar lebih adil)
    stage_equivalent = (state.sector - 1) * 10 + state.substage
    return max(1, int(stage_equivalent * CORE_PER_STAGE))


def do_prestige(state) -> str:
    if not can_prestige(state):
        need = PRESTIGE_STAGE_REQ - state.sector
        return f"RECOMPILE DENIED. Reach Sector {PRESTIGE_STAGE_REQ} (need {need} more)."

    core = get_core_gain(state)
    player = state.player

    player.recompile_count += 1
    player.core_points += core

    # Reset stats
    player.level = 1
    player.exp = 0
    player.hp = 100
    player.max_hp = 100
    player.atk = 5
    player.defense = 1
    player.crit_rate = 0.05
    player.crit_damage = 1.5
    player.gold = 0
    player.gems = 0
    player.dps = 0
    player.inventory = []
    player.agents = []
    player.atk_upgrade_lvl = 0
    player.def_upgrade_lvl = 0
    player.hp_upgrade_lvl = 0
    player.crit_upgrade_lvl = 0

    state.sector = 1
    state.substage = 1
    state.kills_in_stage = 0
    state.boss_active = False
    state.boss_timer = 0.0
    state.enemy = Enemy.generate(state.sector, state.substage, state.player)

    event_logger.emit("recompile", f"RECOMPILE #{player.recompile_count}! +{core} CORE (total: {player.core_points})")

    from game.achievement_tracker import check_and_unlock
    check_and_unlock(state)

    return f"RECOMPILE #{player.recompile_count} COMPLETE.\n+{core} Core Points (total: {player.core_points})\nAll systems reset. Permanent bonuses active."

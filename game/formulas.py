"""
Formulas engine - stateless, balanced for idle gameplay.
"""
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.registry import UpgradeDef, AgentDef


# ─── ENEMY FORMULAS ───────────────────────────

def enemy_hp(stage: int, base_hp: float = 50, growth: float = 1.12) -> int:
    """Enemy HP scales softly per stage."""
    return max(10, int(base_hp * (growth ** stage)))


def enemy_atk(stage: int, base_atk: float = 3, growth: float = 1.08) -> int:
    """Enemy ATK scales slowly."""
    return max(1, int(base_atk * (growth ** stage)))


def enemy_gold(stage: int, base_gold: float = 8, growth: float = 1.10) -> int:
    """Gold reward scales with stage."""
    return max(1, int(base_gold * (growth ** stage)))


def enemy_exp(stage: int, base_exp: float = 4, growth: float = 1.09) -> int:
    """EXP reward scales with stage."""
    return max(1, int(base_exp * (growth ** stage)))


# ─── COMBAT FORMULAS ──────────────────────────

def combat_damage(atk: int, dps: int, defense: int) -> int:
    """
    Player damage to enemy.
    Base ATK + DPS, reduced by enemy defense (~30-60% reduction).
    """
    raw = atk + dps
    reduction = min(0.6, defense / (defense + 50))
    return max(1, int(raw * (1.0 - reduction)))


def enemy_damage(enemy_atk: int, player_def: int) -> int:
    """
    Enemy damage to player.
    40-80% of enemy ATK, reduced by player defense.
    """
    raw = enemy_atk * random.uniform(0.4, 0.8)  # nosec B311
    reduction = min(0.6, player_def / (player_def + 80))
    return max(1, int(raw * (1.0 - reduction)))


def apply_crit(damage: int, crit_rate: float, crit_damage: float) -> int:
    """Critical hit chance."""
    if random.random() < min(crit_rate, 0.95):  # nosec B311 — cap 95%
        return int(damage * max(1.2, crit_damage))
    return damage


# ─── ECONOMY FORMULAS ─────────────────────────

def upgrade_cost(upgrade: 'UpgradeDef', level: int) -> int:
    """Cost to upgrade a stat. Caps at level 1000."""
    level = min(level, 1000)
    return int(upgrade.base_cost * (upgrade.cost_growth ** level))


def agent_cost(agent_def: 'AgentDef', num_owned: int) -> int:
    """Cost to recruit next agent of this type."""
    num_owned = min(num_owned, 500)
    growth = getattr(agent_def, 'cost_growth_per_agent', 1.5)
    return int(agent_def.base_cost * (growth ** num_owned))

def pet_cost(agent_def, num_owned):
    """Backward compatibility wrapper."""
    return agent_cost(agent_def, num_owned)

def required_exp(level: int, base: float = 20, growth: float = 1.18) -> int:
    """EXP needed to reach next level."""
    return int(base * (growth ** (level - 1)))


def offline_gold(dps: int, elapsed_seconds: float) -> int:
    """Gold earned while offline."""
    return int(dps * elapsed_seconds * 0.5)  # 50% efficiency offline


# ─── BOSS SCALING ─────────────────────────────

def boss_hp_multiplier() -> float:
    """Boss HP multiplier: 2.5x - 4x normal enemy."""
    return random.uniform(2.5, 4.0)  # nosec B311


def boss_atk_multiplier() -> float:
    """Boss ATK multiplier: 1.3x - 1.8x normal enemy."""
    return random.uniform(1.3, 1.8)  # nosec B311


def boss_reward_multiplier() -> float:
    """Boss reward multiplier: 2.5x - 3.5x normal enemy."""
    return random.uniform(2.5, 3.5)  # nosec B311

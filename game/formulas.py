"""
Formulas engine - stateless, no imports from constants/registry.
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.registry import UpgradeDef, PetDef
import random


def enemy_hp(stage: int, base_hp: float, growth: float) -> int:
    return max(1, int(base_hp * (growth ** stage)))


def enemy_gold(stage: int, base_gold: float, growth: float) -> int:
    return max(1, int(base_gold * (growth ** stage)))


def enemy_exp(stage: int, base_exp: float, growth: float) -> int:
    return max(1, int(base_exp * (growth ** stage)))


def upgrade_cost(upgrade: 'UpgradeDef', level: int) -> int:
    return int(upgrade.base_cost * (upgrade.cost_growth ** level))


def pet_cost(pet_def: 'PetDef', num_owned: int) -> int:
    return int(pet_def.base_cost * (pet_def.cost_growth_per_pet ** num_owned))


def required_exp(level: int, base: float, growth: float) -> int:
    return int(base * (growth ** (level - 1)))


def combat_damage(atk: int, dps: int, defense: int) -> int:
    return max(1, atk + dps - defense)


def apply_crit(damage: int, crit_rate: float, crit_damage: float) -> int:
    if random.random() < crit_rate:
        return int(damage * crit_damage)
    return damage


def offline_gold(dps: int, elapsed_seconds: float):
    return int(dps * elapsed_seconds)


def enemy_atk(stage: int, base_atk: float, growth: float) -> int:
    return max(1, int(base_atk * (growth ** stage)))


def enemy_damage(enemy_atk: int, player_def: int) -> int:
    return max(1, enemy_atk - player_def)

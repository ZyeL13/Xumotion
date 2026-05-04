from dataclasses import dataclass
import random   # # nosec B311
from game.constants import (
    BASE_ENEMY_HP, ENEMY_HP_GROWTH,
    BASE_GOLD_REWARD, GOLD_REWARD_GROWTH,
    BASE_EXP_REWARD, EXP_REWARD_GROWTH,
    BOSS_INTERVAL, NORMAL_ENEMIES, BOSS_NAMES,
    ENEMY_BASE_ATK, ENEMY_ATK_GROWTH,
)
from game.formulas import enemy_hp, enemy_gold, enemy_exp, enemy_atk


@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    atk: int = 0
    defense: int = 0
    reward_gold: int = 0
    reward_exp: int = 0
    rarity: str = "normal"

    @classmethod
    def generate(cls, stage: int) -> "Enemy":
        is_boss = (stage % BOSS_INTERVAL == 0)
        if is_boss:
            name = random.choice(BOSS_NAMES) + f" {stage}"
            rarity = "prime"
        else:
            name = random.choice(NORMAL_ENEMIES) + f" {stage}"
            rarity = "normal"

        hp = enemy_hp(stage, BASE_ENEMY_HP, ENEMY_HP_GROWTH)
        gold = enemy_gold(stage, BASE_GOLD_REWARD, GOLD_REWARD_GROWTH)
        exp = enemy_exp(stage, BASE_EXP_REWARD, EXP_REWARD_GROWTH)
        atk = enemy_atk(stage, ENEMY_BASE_ATK, ENEMY_ATK_GROWTH)
        return cls(
            name=name,
            hp=hp,
            max_hp=hp,
            reward_gold=gold,
            reward_exp=exp,
            rarity=rarity,
            atk=atk,
        )

    @classmethod
    def generate_prime(cls, stage: int) -> "Enemy":
        """Generate a prime (boss) enemy regardless of stage."""
        name = random.choice(BOSS_NAMES) + " PRIME"
        hp = enemy_hp(stage, BASE_ENEMY_HP, ENEMY_HP_GROWTH) * 2
        gold = enemy_gold(stage, BASE_GOLD_REWARD, GOLD_REWARD_GROWTH) * 3
        exp = enemy_exp(stage, BASE_EXP_REWARD, EXP_REWARD_GROWTH) * 3
        atk = enemy_atk(stage, ENEMY_BASE_ATK, ENEMY_ATK_GROWTH) * 1.5

        return cls(
            name=name,
            hp=hp,
            max_hp=hp,
            reward_gold=gold,
            reward_exp=exp,
            rarity="prime",
            atk=int(atk),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "defense": self.defense,
            "reward_gold": self.reward_gold,
            "reward_exp": self.reward_exp,
            "rarity": self.rarity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Enemy":
        return cls(**data)

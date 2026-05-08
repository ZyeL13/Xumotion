from dataclasses import dataclass
import random  # nosec B311 — gameplay randomness only
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.player import Player

# Nama pool tetap
NORMAL_NAMES = [
    "Echo Fragment", "Corrupt Process", "Forked Instance",
    "Phantom Thread", "Rogue Worker", "Memory Leak"
]
BOSS_NAMES = ["Validator Prime", "Deadlock Core", "Archive Warden"]

# Base rewards per sector (nilai minimal, akan diskalakan)
BASE_GOLD = 10
BASE_EXP = 5
GOLD_SECTOR_GROWTH = 1.10   # per sektor
EXP_SECTOR_GROWTH = 1.08


@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    atk: int = 0
    defense: int = 0
    reward_gold: int = 0
    reward_exp: int = 0
    rarity: str = "normal"   # "normal" or "boss"

    @classmethod
    def generate(cls, sector: int, substage: int, player: "Player") -> "Enemy":
        """Generate normal or boss enemy with hybrid scaling."""
        # 1. Tentukan tipe
        is_boss = (substage == 10)
        rarity = "boss" if is_boss else "normal"
        name_pool = BOSS_NAMES if is_boss else NORMAL_NAMES
        name = random.choice(name_pool)  # nosec B311

        # 2. Baseline sektor (sedikit peningkatan per sektor)
        sector_mult = 1.0 + (sector - 1) * 0.05

        # 3. Multiplier dalam sektor (1.00 → 1.25)
        encounter_mult = 1.0 + (substage - 1) * 0.03

        # 4. Stat relatif terhadap pemain
        hp_rel = random.uniform(1.2, 1.8)   # nosec B311
        atk_rel = random.uniform(0.85, 1.15) # nosec B311
        def_rel = random.uniform(0.8, 1.1)   # nosec B311

        base_hp = int(player.max_hp * hp_rel * sector_mult * encounter_mult)
        base_atk = int(player.atk * atk_rel * sector_mult * encounter_mult)
        base_def = int(player.defense * def_rel * sector_mult * encounter_mult)

        # 5. Boss dibuff lebih kuat
        if is_boss:
            hp_mult = random.uniform(2.5, 3.5)   # nosec B311
            atk_mult = random.uniform(1.4, 1.8)   # nosec B311
            def_mult = random.uniform(1.3, 1.6)   # nosec B311
            hp = int(base_hp * hp_mult)
            atk = int(base_atk * atk_mult)
            defense = int(base_def * def_mult)
        else:
            hp = base_hp
            atk = base_atk
            defense = base_def

        # 6. Hitung stage untuk reward (biar reward tetap terasa progresif)
        stage = (sector - 1) * 10 + substage
        gold = int(BASE_GOLD * (GOLD_SECTOR_GROWTH ** sector) * encounter_mult)
        exp = int(BASE_EXP * (EXP_SECTOR_GROWTH ** sector) * encounter_mult)
        if is_boss:
            gold = int(gold * 2.5)
            exp = int(exp * 3)

        return cls(
            name=name,
            hp=hp,
            max_hp=hp,
            atk=atk,
            defense=defense,
            reward_gold=gold,
            reward_exp=exp,
            rarity=rarity,
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

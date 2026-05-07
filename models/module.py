from dataclasses import dataclass
from enum import Enum


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class Slot(Enum):
    INJECTOR = "injector"
    BARRIER = "barrier"
    CACHE = "cache"


RARITY_STAT_MULTIPLIER = {
    Rarity.COMMON: 1.0,
    Rarity.UNCOMMON: 1.5,
    Rarity.RARE: 2.0,
    Rarity.EPIC: 3.0,
    Rarity.LEGENDARY: 5.0,
}

RARITY_COLOR = {
    Rarity.COMMON: "white",
    Rarity.UNCOMMON: "green",
    Rarity.RARE: "blue",
    Rarity.EPIC: "purple",
    Rarity.LEGENDARY: "gold",
}


@dataclass
class Module:
    name: str
    slot: Slot
    rarity: Rarity
    atk_bonus: int = 0
    def_bonus: int = 0
    hp_bonus: int = 0
    crit_rate_bonus: float = 0.0
    installed: bool = False

    def __post_init__(self):
        mult = RARITY_STAT_MULTIPLIER[self.rarity]
        self.atk_bonus = int(self.atk_bonus * mult)
        self.def_bonus = int(self.def_bonus * mult)
        self.hp_bonus = int(self.hp_bonus * mult)
        self.crit_rate_bonus = round(self.crit_rate_bonus * mult, 3)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "slot": self.slot.value,
            "rarity": self.rarity.value,
            "atk_bonus": self.atk_bonus,
            "def_bonus": self.def_bonus,
            "hp_bonus": self.hp_bonus,
            "crit_rate_bonus": self.crit_rate_bonus,
            "installed": self.installed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Module":
        rarity = Rarity(data["rarity"])
        slot = Slot(data["slot"])
        eq = cls(
            name=data["name"],
            slot=slot,
            rarity=rarity,
            atk_bonus=data["atk_bonus"],
            def_bonus=data["def_bonus"],
            hp_bonus=data["hp_bonus"],
            crit_rate_bonus=data["crit_rate_bonus"],
            installed=data.get("installed", False),
        )
        eq.atk_bonus = data["atk_bonus"]
        eq.def_bonus = data["def_bonus"]
        eq.hp_bonus = data["hp_bonus"]
        eq.crit_rate_bonus = data["crit_rate_bonus"]
        return eq

from dataclasses import dataclass, field
from typing import List
from models.pet import Agent
from models.module import Module


@dataclass
class Player:
    level: int = 1
    exp: int = 0
    hp: int = 100
    max_hp: int = 100
    atk: int = 5
    defense: int = 1
    crit_rate: float = 0.05
    crit_damage: float = 1.5
    gold: int = 0
    gems: int = 0
    dps: int = 0
    inventory: list = field(default_factory=list)
    agents: List[Agent] = field(default_factory=list)

    # upgrade levels (how many times each was purchased)
    atk_upgrade_lvl: int = 0
    def_upgrade_lvl: int = 0
    hp_upgrade_lvl: int = 0
    crit_upgrade_lvl: int = 0

    core_points: int = 0
    core_spent: int = 0
    recompile_count: int = 0
    auto_enhance: bool = False

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "exp": self.exp,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "defense": self.defense,
            "crit_rate": self.crit_rate,
            "crit_damage": self.crit_damage,
            "gold": self.gold,
            "gems": self.gems,
            "dps": self.dps,
            "inventory": [item.to_dict() for item in self.inventory],
            "agents": [a.to_dict() for a in self.agents],
            "atk_upgrade_lvl": self.atk_upgrade_lvl,
            "def_upgrade_lvl": self.def_upgrade_lvl,
            "hp_upgrade_lvl": self.hp_upgrade_lvl,
            "crit_upgrade_lvl": self.crit_upgrade_lvl,
            "core_points": self.core_points,
            "core_spent": self.core_spent,
            "recompile_count": self.recompile_count,
            "auto_enhance": self.auto_enhance,
        }
    @property
    def total_atk(self) -> int:
        """ATK after prestige multiplier."""
        mult = 1.0 + (self.core_points * 0.05)
        return int(self.atk * mult)

    @property
    def effective_def(self) -> float:
        return self.defense * (1.0 + self.core_points * 0.05)

    @property
    def effective_max_hp(self) -> int:
        return int(self.max_hp * (1.0 + self.core_points * 0.05))

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        player = cls(
            level=data["level"],
            exp=data["exp"],
            hp=data["hp"],
            max_hp=data["max_hp"],
            atk=data["atk"],
            defense=data["defense"],
            crit_rate=data["crit_rate"],
            crit_damage=data["crit_damage"],
            gold=data["gold"],
            gems=data["gems"],
            dps=data["dps"],
            inventory=[Module.from_dict(item) for item in data.get("inventory", [])],
            atk_upgrade_lvl=data.get("atk_upgrade_lvl", 0),
            def_upgrade_lvl=data.get("def_upgrade_lvl", 0),
            hp_upgrade_lvl=data.get("hp_upgrade_lvl", 0),
            crit_upgrade_lvl=data.get("crit_upgrade_lvl", 0),
            core_points=data.get("core_points", 0),
            core_spent=data.get("core_spent", 0),
            recompile_count=data.get("recompile_count", 0),
            auto_enhance=data.get("auto_enhance", False),
        )
        player.agents = [Agent.from_dict(a) for a in data.get("agents", [])]  # ✅
        return player

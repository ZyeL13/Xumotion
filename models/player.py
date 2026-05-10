from dataclasses import dataclass, field
from typing import List
from models.agent import Agent
from models.module import Module


@dataclass
class Player:
    level: int = 1
    exp: int = 0
    hp: int = 300
    max_hp: int = 300
    atk: int = 50
    defense: int = 3
    crit_rate: float = 0.05
    crit_damage: float = 1.5
    gold: int = 0
    gems: int = 0
    dps: int = 0
    inventory: list = field(default_factory=list)
    agents: List[Agent] = field(default_factory=list)
    last_daily_claim: float = 0.0

    # upgrade levels
    atk_upgrade_lvl: int = 0
    def_upgrade_lvl: int = 0
    hp_upgrade_lvl: int = 0
    crit_upgrade_lvl: int = 0

    # core/prestige
    core_points: int = 0
    core_spent: int = 0
    recompile_count: int = 0

    # automation
    auto_enhance: bool = False

    # NEW currency
    input_credits: int = 0

    def get_deployed_count(self) -> int:
        return sum(1 for a in self.agents if a.deployed)

    def get_available_slots(self) -> int:
        return max(0, self.max_agent_slots - self.get_deployed_count())

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
            "input_credits": self.input_credits,
            "last_daily_claim": self.last_daily_claim,
        }

    @property
    def total_atk(self) -> int:
        mult = 1.0 + (self.core_points * 0.05)
        return int(self.atk * mult)

    @property
    def effective_def(self) -> float:
        return self.defense * (1.0 + self.core_points * 0.05)

    @property
    def effective_max_hp(self) -> int:
        return int(self.max_hp * (1.0 + self.core_points * 0.05))

    @property
    def max_agent_slots(self) -> int:
        base = 2
        rank_bonus = self.level // 15
        recompile_bonus = self.recompile_count // 3
        return base + rank_bonus + recompile_bonus

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
            input_credits=data.get("input_credits", 0),
            last_daily_claim=data.get("last_daily_claim", 0),
        )
        player.agents = [Agent.from_dict(a) for a in data.get("agents", [])]
        return player

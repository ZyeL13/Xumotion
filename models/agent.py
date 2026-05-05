from dataclasses import dataclass


@dataclass
class Agent:
    name: str
    tier: str              # "common", "rare", "epic", "prime"
    dps: int                # current DPS (after enhance)
    base_dps: int           # base DPS (used for calculations)
    level: int = 1          # enhance level
    deployed: bool = False  # active in slot?

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tier": self.tier,
            "dps": self.dps,
            "base_dps": self.base_dps,
            "level": self.level,
            "deployed": self.deployed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        return cls(
            name=data["name"],
            tier=data.get("tier", "common"),
            dps=data.get("dps", data.get("base_dps", 1)),
            base_dps=data.get("base_dps", data.get("dps", 1)),
            level=data.get("level", 1),
            deployed=data.get("deployed", False),
        )

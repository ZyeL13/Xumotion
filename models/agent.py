from dataclasses import dataclass


import uuid

@dataclass
class Agent:
    id: str                 # ID unik (6‑char hex)
    name: str
    tier: str
    dps: int
    base_dps: int
    level: int = 1
    deployed: bool = False

    @staticmethod
    def generate_id() -> str:
        return uuid.uuid4().hex[:6].upper()  # contoh: "A1B2C3"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
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
            id=data.get("id", Agent.generate_id()),
            name=data["name"],
            tier=data.get("tier", "common"),
            dps=data.get("dps", 3),
            base_dps=data.get("base_dps", 3),
            level=data.get("level", 1),
            deployed=data.get("deployed", False),
        )

from dataclasses import dataclass


@dataclass
class Agent:
    name: str
    dps: int

    def to_dict(self) -> dict:
        return {"name": self.name, "dps": self.dps}

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        return cls(name=data["name"], dps=data["dps"])

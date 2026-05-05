"""
Content pipeline – load semua data dari folder data/
"""
import json
from pathlib import Path
from typing import Dict, Any

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> Dict[str, Any]:
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def load_enemies() -> dict:
    return _load_json("enemies.json")


def load_upgrades() -> dict:
    return _load_json("upgrades.json")


def load_pets() -> dict:
    return _load_json("agents.json")

def load_agents() -> dict:
    return _load_json("agents.json")

def load_progression() -> dict:
    return _load_json("progression.json")

"""
Content pipeline – load & validate data dari folder data/
"""
import json
from pathlib import Path
from typing import Dict, Any

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> Dict[str, Any]:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {filename}")
    with open(path, "r") as f:
        return json.load(f)


def load_enemies() -> dict:
    data = _load_json("enemies.json")

    # Validasi scaling
    scaling = data.get("scaling", {})
    required_scaling = ["base_hp", "hp_growth", "base_gold", "gold_growth",
                        "base_exp", "exp_growth", "base_atk", "atk_growth"]
    for key in required_scaling:
        if key not in scaling:
            raise ValueError(f"enemies.json: scaling.{key} is missing")
        if not isinstance(scaling[key], (int, float)):
            raise ValueError(f"enemies.json: scaling.{key} must be a number")
        if scaling[key] <= 0:
            raise ValueError(f"enemies.json: scaling.{key} must be positive")

    # Validasi nama
    if "normal_names" not in data or not isinstance(data["normal_names"], list):
        raise ValueError("enemies.json: normal_names must be a list")
    if "boss_names" not in data or not isinstance(data["boss_names"], list):
        raise ValueError("enemies.json: boss_names must be a list")
    if "boss_interval" not in data or not isinstance(data["boss_interval"], int):
        raise ValueError("enemies.json: boss_interval must be an integer")

    return data


def load_upgrades() -> dict:
    data = _load_json("upgrades.json")
    required_keys = ["atk", "defense", "max_hp", "crit_rate"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"upgrades.json: missing upgrade '{key}'")
        upgrade = data[key]
        for field in ["base_cost", "growth", "increment"]:
            if field not in upgrade:
                raise ValueError(f"upgrades.json: {key}.{field} missing")
            if not isinstance(upgrade[field], (int, float)):
                raise ValueError(f"upgrades.json: {key}.{field} must be a number")
        if upgrade["base_cost"] < 0:
            raise ValueError(f"upgrades.json: {key}.base_cost must be non-negative")
        if upgrade["growth"] < 1.0:
            raise ValueError(f"upgrades.json: {key}.growth must be >= 1.0")
    return data


def load_agents() -> dict:
    data = _load_json("agents.json")
    valid_tiers = ["common", "rare", "epic", "prime"]
    if not isinstance(data, dict):
        raise ValueError("agents.json: must be a JSON object")

    for tier, agents in data.items():
        if tier not in valid_tiers:
            raise ValueError(f"agents.json: unknown tier '{tier}', allowed: {valid_tiers}")
        if not isinstance(agents, list):
            raise ValueError(f"agents.json: tier '{tier}' must be a list of agents")
        for idx, agent in enumerate(agents):
            for field in ["id", "name", "tier", "base_dps", "base_cost"]:
                if field not in agent:
                    raise ValueError(f"agents.json: agent {idx+1} in tier '{tier}' missing '{field}'")
            if not isinstance(agent["base_dps"], (int, float)) or agent["base_dps"] <= 0:
                raise ValueError(f"agents.json: agent '{agent.get('name', idx+1)}' has invalid base_dps")
            if not isinstance(agent["base_cost"], (int, float)) or agent["base_cost"] <= 0:
                raise ValueError(f"agents.json: agent '{agent.get('name', idx+1)}' has invalid base_cost")
    return data


def load_pets() -> dict:
    """Alias untuk backward compatibility."""
    return load_agents()


def load_progression() -> dict:
    data = _load_json("progression.json")
    # Level EXP
    level_exp = data.get("level_exp", {})
    if not isinstance(level_exp.get("base"), (int, float)) or level_exp["base"] <= 0:
        raise ValueError("progression.json: level_exp.base must be positive")
    if not isinstance(level_exp.get("growth"), (int, float)) or level_exp["growth"] < 1.0:
        raise ValueError("progression.json: level_exp.growth must be >= 1.0")

    # Level-up rewards
    rewards = data.get("level_up_rewards", {})
    if not isinstance(rewards.get("atk_increase"), (int, float)) or rewards["atk_increase"] < 0:
        raise ValueError("progression.json: level_up_rewards.atk_increase must be non-negative")
    if not isinstance(rewards.get("max_hp_increase"), (int, float)) or rewards["max_hp_increase"] < 0:
        raise ValueError("progression.json: level_up_rewards.max_hp_increase must be non-negative")

    # Offline cap
    offcap = data.get("offline_cap_seconds", 28800)
    if not isinstance(offcap, (int, float)) or offcap < 0:
        raise ValueError("progression.json: offline_cap_seconds must be non-negative")

    # Prestige
    prestige = data.get("prestige", {})
    for key in ["stage_requirement", "core_per_stage", "credits_mult_per_core",
                "exp_mult_per_core", "atk_mult_per_core", "def_mult_per_core", "hp_mult_per_core"]:
        if key not in prestige:
            raise ValueError(f"progression.json: prestige.{key} is missing")
        if not isinstance(prestige[key], (int, float)):
            raise ValueError(f"progression.json: prestige.{key} must be a number")
    if prestige["stage_requirement"] < 1:
        raise ValueError("progression.json: prestige.stage_requirement must be >= 1")

    return data

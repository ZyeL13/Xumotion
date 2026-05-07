"""
Registry pattern - UPGRADE_REGISTRY and AGENT_REGISTRY.
Loads raw data from constants.py (UPGRADE_DATA, AGENT_DEFINITIONS).
"""
from dataclasses import dataclass
from typing import Dict, Callable
from game.constants import UPGRADE_DATA, AGENT_DEFINITIONS


@dataclass
class UpgradeDef:
    key: str
    name: str
    base_cost: int
    cost_growth: float
    increment: float
    apply: Callable


@dataclass
class AgentDef:
    agent_id: str
    name: str
    tier: str
    base_dps: int
    base_cost: int
    cost_growth_per_agent: float
    enhance_cost_base: int
    enhance_cost_growth: float


# ---------- Apply functions ----------
def _apply_atk(player, inc):
    player.atk += int(inc)

def _apply_def(player, inc):
    player.defense += int(inc)

def _apply_max_hp(player, inc):
    player.max_hp += int(inc)
    player.hp = player.max_hp

def _apply_crit_rate(player, inc):
    player.crit_rate = min(1.0, player.crit_rate + inc)


# ---------- Build Upgrade Registry ----------
_upgrade_names = {
    "atk": "ATK",
    "defense": "DEF",
    "max_hp": "Max HP",
    "crit_rate": "Crit Rate",
}
_upgrade_appliers = {
    "atk": _apply_atk,
    "defense": _apply_def,
    "max_hp": _apply_max_hp,
    "crit_rate": _apply_crit_rate,
}

UPGRADE_REGISTRY: Dict[str, UpgradeDef] = {}

for key, cfg in UPGRADE_DATA.items():
    UPGRADE_REGISTRY[key] = UpgradeDef(
        key=key,
        name=_upgrade_names.get(key, key),
        base_cost=cfg.get("base_cost", 10),
        cost_growth=cfg.get("growth", 1.15),
        increment=cfg.get("increment", 1),
        apply=_upgrade_appliers.get(key, _apply_atk),
    )


# ---------- Build Agent Registry ----------
AGENT_REGISTRY: Dict[str, AgentDef] = {}

if AGENT_DEFINITIONS:
    for agent_id, cfg in AGENT_DEFINITIONS.items():
        AGENT_REGISTRY[agent_id] = AgentDef(
            agent_id=agent_id,
            name=cfg.get("name", agent_id),
            tier=cfg.get("tier", "common"),
            base_dps=cfg.get("base_dps", 1),
            base_cost=cfg.get("base_cost", 100),
            cost_growth_per_agent=cfg.get("cost_growth_per_pet", 1.5),
            enhance_cost_base=cfg.get("enhance_cost_base", 50),
            enhance_cost_growth=cfg.get("enhance_cost_growth", 1.35),
        )
else:
    # Fallback single agent
    AGENT_REGISTRY["echo_unit"] = AgentDef(
        agent_id="echo_unit",
        name="Echo Unit",
        tier="common",
        base_dps=3,
        base_cost=80,
        cost_growth_per_agent=1.5,
        enhance_cost_base=50,
        enhance_cost_growth=1.35,
    )

DEFAULT_AGENT_ID = next(iter(AGENT_REGISTRY)) if AGENT_REGISTRY else "echo_unit"

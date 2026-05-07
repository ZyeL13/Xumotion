"""
Game constants - loaded from JSON data files.
NO imports from other game modules (to avoid circular deps).
"""
from game.content import load_enemies, load_upgrades, load_pets, load_progression, load_agents

# Load raw configs
_enemy = load_enemies()
_upgrades = load_upgrades()
_pets = load_pets()
_prog = load_progression()

# Prestige
PRESTIGE_STAGE_REQ = _prog.get("prestige", {}).get("stage_requirement", 50)
CORE_PER_STAGE = _prog.get("prestige", {}).get("core_per_stage", 0.1)
CREDITS_MULT_PER_CORE = _prog.get("prestige", {}).get("credits_mult_per_core", 0.1)
EXP_MULT_PER_CORE = _prog.get("prestige", {}).get("exp_mult_per_core", 0.1)
ATK_MULT_PER_CORE = _prog.get("prestige", {}).get("atk_mult_per_core", 0.05)
DEF_MULT_PER_CORE = _prog.get("prestige", {}).get("def_mult_per_core", 0.05)
HP_MULT_PER_CORE = _prog.get("prestige", {}).get("hp_mult_per_core", 0.05)
# --- Enemy ---
NORMAL_ENEMIES = _enemy.get("normal_names", ["Slime"])
BOSS_NAMES = _enemy.get("boss_names", ["Goblin King"])
BOSS_INTERVAL = _enemy.get("boss_interval", 10)

ENEMY_SCALING = _enemy.get("scaling", {})
BASE_ENEMY_HP = ENEMY_SCALING.get("base_hp", 50)
ENEMY_HP_GROWTH = ENEMY_SCALING.get("hp_growth", 1.18)
BASE_GOLD_REWARD = ENEMY_SCALING.get("base_gold", 10)
GOLD_REWARD_GROWTH = ENEMY_SCALING.get("gold_growth", 1.20)
BASE_EXP_REWARD = ENEMY_SCALING.get("base_exp", 5)
EXP_REWARD_GROWTH = ENEMY_SCALING.get("exp_growth", 1.14)
ENEMY_BASE_DEFENSE = _enemy.get("enemy_base_defense", 0)
ENEMY_BASE_ATK = ENEMY_SCALING.get("base_atk", 3)
ENEMY_ATK_GROWTH = ENEMY_SCALING.get("atk_growth", 1.10)
# --- Upgrades (raw data) ---
UPGRADE_DATA = _upgrades

# --- Agents (raw data) ---
AGENT_RAW = load_agents()

def _flatten_agents(raw: dict) -> dict:
    flat = {}
    for tier, agents in raw.items():
        for agent in agents:
            flat[agent["id"]] = agent
    return flat

AGENT_DEFINITIONS = _flatten_agents(AGENT_RAW)

# Fallback first agent
_first_agent_id = next(iter(AGENT_DEFINITIONS)) if AGENT_DEFINITIONS else None
if _first_agent_id:
    _a = AGENT_DEFINITIONS[_first_agent_id]
    AGENT_NAME = _a.get("name", "Echo Unit")
    AGENT_BASE_COST = _a.get("base_cost", 80)
    AGENT_COST_GROWTH = _a.get("cost_growth_per_pet", 1.5)
    AGENT_BASE_DPS = _a.get("base_dps", 3)
else:
    AGENT_NAME = "Echo Unit"
    AGENT_BASE_COST = 80
    AGENT_COST_GROWTH = 1.5
    AGENT_BASE_DPS = 3

# --- Progression ---
LEVEL_EXP_BASE = _prog.get("level_exp", {}).get("base", 20)
LEVEL_EXP_GROWTH = _prog.get("level_exp", {}).get("growth", 1.2)
ATK_PER_LEVEL = _prog.get("level_up_rewards", {}).get("atk_increase", 2)
HP_PER_LEVEL = _prog.get("level_up_rewards", {}).get("max_hp_increase", 10)
OFFLINE_PROGRESS_CAP = _prog.get("offline_cap_seconds", 28800)

# --- Core timing ---
TICK_RATE = 1.0

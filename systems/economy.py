from game.registry import UPGRADE_REGISTRY, AGENT_REGISTRY, DEFAULT_AGENT_ID
from game.formulas import upgrade_cost, pet_cost
from models.pet import Agent
from game.event_logger import event_logger


def get_upgrade_level(player, key: str) -> int:
    mapping = {
        "atk": player.atk_upgrade_lvl,
        "defense": player.def_upgrade_lvl,
        "max_hp": player.hp_upgrade_lvl,
        "crit_rate": player.crit_upgrade_lvl,
    }
    return mapping.get(key, 0)


def increment_upgrade_level(player, key: str):
    if key == "atk":
        player.atk_upgrade_lvl += 1
    elif key == "defense":
        player.def_upgrade_lvl += 1
    elif key == "max_hp":
        player.hp_upgrade_lvl += 1
    elif key == "crit_rate":
        player.crit_upgrade_lvl += 1


def handle_upgrade(state, target: str) -> str:
    player = state.player
    upgrade = UPGRADE_REGISTRY.get(target)
    if not upgrade:
        return f"UNKNOWN ENHANCE TARGET: '{target}'. Available: {', '.join(UPGRADE_REGISTRY.keys())}"

    current_lvl = get_upgrade_level(player, target)
    cost = upgrade_cost(upgrade, current_lvl)
    if player.gold >= cost:
        player.gold -= cost
        upgrade.apply(player, upgrade.increment)
        increment_upgrade_level(player, target)
        event_logger.emit("enhance", f"MODULE ENHANCED: {upgrade.name} -> level {current_lvl + 1}")
        return f"MODULE ENHANCED: {upgrade.name} +{upgrade.increment}. Level {current_lvl + 1}. Cost: {cost} credits."
    return f"INSUFFICIENT CREDITS. Need {cost}, have {player.gold}."


def get_agent_cost(agent_def, num_owned: int) -> int:
    return pet_cost(agent_def, num_owned)


def deploy_agent(state, agent_id: str = None) -> str:
    player = state.player
    if agent_id is None:
        agent_id = DEFAULT_AGENT_ID

    agent_def = AGENT_REGISTRY.get(agent_id)
    if not agent_def:
        return f"UNKNOWN AGENT: '{agent_id}'."

    num_owned = sum(1 for a in player.agents if a.name.startswith(agent_def.name))
    cost = get_agent_cost(agent_def, num_owned)
    if player.gold >= cost:
        player.gold -= cost
        new_agent = Agent(name=f"{agent_def.name} #{num_owned + 1}", dps=agent_def.base_dps)
        player.agents.append(new_agent)
        event_logger.emit("agent_deployed", f"AGENT DEPLOYED: {new_agent.name}")
        return f"AGENT DEPLOYED: {new_agent.name} (DPS +{new_agent.dps})."
    return f"INSUFFICIENT CREDITS. Agent costs {cost}, you have {player.gold}."

def enhance_agent(state, agent_name: str) -> str:
    """Enhance a deployed agent's DPS. Supports name with optional number."""
    player = state.player
    
    # Parse name and optional number
    parts = agent_name.rsplit(None, 1)
    target_name = parts[0]
    target_num = None
    
    if len(parts) == 2 and parts[1].isdigit():
        target_num = int(parts[1])
    elif len(parts) == 1 and parts[0].isdigit():
        # User gave only number, like "/ea 3"
        target_num = int(parts[0])
        target_name = None
    
    # Find matching agents
    matches = []
    for agent in player.agents:
        if target_name and target_name.lower() in agent.name.lower():
            matches.append(agent)
        elif target_num and str(target_num) in agent.name.split("#")[-1]:
            matches.append(agent)
    
    if not matches:
        return f"Agent not found. Use '/ea <name>' or '/ea <number>'."
    
    # If number specified, target that one
    target = None
    if target_num:
        for agent in matches:
            try:
                agent_num = int(agent.name.split("#")[-1].strip())
                if agent_num == target_num:
                    target = agent
                    break
            except:
                pass
    
    if not target and matches:
        target = matches[0]  # fallback to first match
    
    if not target:
        return f"Agent not found."
    
    cost = int(target.dps * 25)
    if player.gold >= cost:
        player.gold -= cost
        target.dps += 2
        event_logger.emit("agent_enhance", f"AGENT ENHANCED: {target.name} -> DPS {target.dps}")
        return f"AGENT ENHANCED: {target.name} now DPS {target.dps}. Cost: {cost} credits."
    return f"INSUFFICIENT CREDITS. Need {cost}, have {player.gold}."

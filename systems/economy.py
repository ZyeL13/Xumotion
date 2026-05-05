from game.registry import UPGRADE_REGISTRY, AGENT_REGISTRY, DEFAULT_AGENT_ID
from game.formulas import upgrade_cost, pet_cost
from models.agent import Agent
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
    """Deploy a new agent. If slot available, auto-deploy."""
    player = state.player
    if agent_id is None:
        agent_id = DEFAULT_AGENT_ID

    agent_def = AGENT_REGISTRY.get(agent_id)
    if not agent_def:
        return f"UNKNOWN AGENT: '{agent_id}'."

    # Count owned agents of this type
    num_owned = sum(1 for a in player.agents if a.name.startswith(agent_def.name))
    cost = get_agent_cost(agent_def, num_owned)
    if player.gold < cost:
        return f"INSUFFICIENT CREDITS. Agent costs {cost}, you have {player.gold}."

    # Create agent
    player.gold -= cost
    new_agent = Agent(
        id=Agent.generate_id(),
        name=f"{agent_def.name} #{num_owned + 1}",
        tier=agent_def.tier,
        dps=agent_def.base_dps,
        base_dps=agent_def.base_dps,
        level=1,
        deployed=False,
    )
    player.agents.append(new_agent)

    # Auto-deploy if slots available
    if player.get_available_slots() > 0:
        new_agent.deployed = True
        event_logger.emit("agent_deployed", f"AGENT DEPLOYED: {new_agent.name} (slot {player.get_deployed_count()}/{player.max_agent_slots})")
        return f"AGENT DEPLOYED: {new_agent.name} (DPS +{new_agent.dps}). [{player.get_deployed_count()}/{player.max_agent_slots} slots]"
    else:
        event_logger.emit("agent_acquired", f"AGENT ACQUIRED: {new_agent.name} (in bay, no slot)")
        return f"AGENT ACQUIRED: {new_agent.name} (DPS {new_agent.dps}). No deployment slot available. Use /deploy <name> to manage slots."


def undeploy_agent(state, agent_name: str) -> str:
    """Remove agent from active slot."""
    player = state.player
    target = None
    for agent in player.agents:
        if agent.deployed and (agent_name.lower() in agent.name.lower() or agent_name in agent.name.split("#")[-1]):
            target = agent
            break
    if not target:
        return f"Agent '{agent_name}' not found or not deployed."
    target.deployed = False
    event_logger.emit("agent_undeployed", f"AGENT UNDEPLOYED: {target.name}")
    return f"AGENT UNDEPLOYED: {target.name}. Slot freed ({player.get_deployed_count()}/{player.max_agent_slots})."


def deploy_specific_agent(state, agent_name: str) -> str:
    """Activate a specific owned agent into a free slot."""
    player = state.player
    if player.get_available_slots() <= 0:
        return "No free agent slots. Unslot an active agent first."
    target = None
    for agent in player.agents:
        if not agent.deployed and (agent_name.lower() in agent.name.lower() or agent_name in agent.name.split("#")[-1]):
            target = agent
            break
    if not target:
        return f"Inactive agent '{agent_name}' not found."
    target.deployed = True
    event_logger.emit("agent_deployed", f"AGENT DEPLOYED: {target.name}")
    return f"AGENT DEPLOYED: {target.name}. [{player.get_deployed_count()}/{player.max_agent_slots}]"


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
        target_num = int(parts[0])
        target_name = None
    
    matches = []
    for agent in player.agents:
        if target_name and target_name.lower() in agent.name.lower():
            matches.append(agent)
        elif target_num and str(target_num) in agent.name.split("#")[-1]:
            matches.append(agent)
    
    if not matches:
        return f"Agent not found. Use '/ea <name>' or '/ea <number>'."
    
    target = None
    if target_num:
        for agent in matches:
            try:
                agent_num = int(agent.name.split("#")[-1].strip())
                if agent_num == target_num:
                    target = agent
                    break
            except Exception:
                pass
    
    if not target and matches:
        target = matches[0]
    
    if not target:
        return f"Agent not found."
    
    # Enhance cost based on agent's level and tier
    cost = int(50 * (1.35 ** (target.level - 1)))
    if player.gold >= cost:
        player.gold -= cost
        target.level += 1
        target.dps = int(target.base_dps * (1.2 ** (target.level - 1)))  # 20% increase per level
        event_logger.emit("agent_enhance", f"AGENT ENHANCED: {target.name} -> Lv.{target.level} DPS {target.dps}")
        return f"AGENT ENHANCED: {target.name} Lv.{target.level} now DPS {target.dps}. Cost: {cost} credits."

def merge_agents(state, unit_name: str, *agent_ids: str) -> str:
    """Merge 3 agents of the same tier into one higher-tier agent.
    Usage: merge <unit_name> <id1> <id2> <id3>
    - unit_name: filter by agent name (e.g., "Echo", "Cache"), or None for old format
    - id1, id2, id3: agent ID (hex), name, hashtag number, or list index (1-based)
    """
    player = state.player
    
    if len(agent_ids) != 3:
        return "MERGE requires exactly 3 agents of the same tier."
    
    # Cari agent berdasarkan id (ID, nama lengkap, hashtag, atau indeks list)
    targets: list = []
    for aid in agent_ids:
        found = None
        
        # Coba 0: cocokkan ID persis (case-insensitive)  <-- TAMBAHAN
        if not found:
            for agent in player.agents:
                if aid.upper() == agent.id.upper():
                    found = agent
                    break
        
        # Coba 1: cocokkan nama lengkap (case-insensitive)
        if not found:
            for agent in player.agents:
                if aid.lower() == agent.name.lower():
                    found = agent
                    break
        
        # Coba 2: cocokkan nomor hashtag di belakang #
        if not found:
            for agent in player.agents:
                tag = agent.name.split("#")[-1].strip()
                if aid == tag:
                    found = agent
                    break
        
        # Coba 3: treat aid as 1-based index into player.agents list
        if not found and aid.isdigit():
            idx = int(aid)
            if 1 <= idx <= len(player.agents):
                found = player.agents[idx - 1]  # convert 1-based to 0-based
        
        if not found:
            return f"Agent '{aid}' not found. Use agent name, hashtag number, list index, or agent ID."
        if found in targets:
            return f"Duplicate agent '{aid}'."
        targets.append(found)
    
    # Validasi nama unit jika diberikan
    if unit_name and unit_name.strip():
        for agent in targets:
            if unit_name.lower() not in agent.name.lower():
                return f"Agent '{agent.name}' does not match unit type '{unit_name}'. All agents must be '{unit_name}'."
    
    # Validasi tier sama
    tiers = {agent.tier for agent in targets}
    if len(tiers) != 1:
        return "All 3 agents must have the SAME tier to merge."
    current_tier = targets[0].tier
    
    # Urutan tier
    tier_order = {"common": 0, "rare": 1, "epic": 2, "prime": 3}
    if current_tier not in tier_order or current_tier == "prime":
        return "Cannot merge PRIME agents further."
    
    next_tier = {0: "rare", 1: "epic", 2: "prime"}[tier_order[current_tier]]
    
    # Cari agent_def untuk tier berikutnya
    next_def = None
    for agent_id, defn in AGENT_REGISTRY.items():
        if defn.tier == next_tier:
            next_def = defn
            break
    if not next_def:
        return f"No agent definition found for tier '{next_tier}'."
    
    # Hapus 3 agent
    for agent in targets:
        if agent.deployed:
            agent.deployed = False
        player.agents.remove(agent)
    
    # Buat agent baru
    num_owned = sum(1 for a in player.agents if a.name.startswith(next_def.name))
    new_agent = Agent(
        id=Agent.generate_id(),
        name=f"{next_def.name} #{num_owned + 1}",
        tier=next_tier,
        dps=next_def.base_dps,
        base_dps=next_def.base_dps,
        level=1,
        deployed=False,
    )
    player.agents.append(new_agent)
    
    if player.get_available_slots() > 0:
        new_agent.deployed = True
    
    event_logger.emit("agent_merged", f"MERGE: {targets[0].name}+{targets[1].name}+{targets[2].name} → {new_agent.name} ({new_agent.tier})")
    status = "auto-deployed" if new_agent.deployed else "in bay"
    return f"MERGE COMPLETE: {new_agent.name} ({new_agent.tier}, DPS {new_agent.dps}) {status}."

def auto_merge(state) -> str:
    """Gabung 3 agent tier sama yang nggak deployed. Return pesan atau string kosong."""
    player = state.player
    
    tier_groups = {}
    for agent in player.agents:
        tier = agent.tier
        if tier not in tier_groups:
            tier_groups[tier] = []
        tier_groups[tier].append(agent)
    
    for tier in ("common", "rare", "epic"):
        agents = tier_groups.get(tier, [])
        if len(agents) >= 3:
            agents_sorted = sorted(agents, key=lambda a: a.deployed)
            a1, a2, a3 = agents_sorted[:3]
            
            # Gunakan ID unik agent
            result = merge_agents(state, "", a1.id, a2.id, a3.id)
            return result
    
    return ""

def auto_deploy_best(state) -> str:
    """Isi slot kosong dengan agen terbaik yang belum deployed."""
    player = state.player
    available_slots = player.get_available_slots()
    if available_slots <= 0:
        return ""

    # Kumpulkan agen yang tidak deployed, urutkan berdasarkan DPS tertinggi
    inactive = [a for a in player.agents if not a.deployed]
    if not inactive:
        return ""

    inactive.sort(key=lambda a: a.dps, reverse=True)
    deployed_list = []
    for agent in inactive[:available_slots]:
        agent.deployed = True
        deployed_list.append(agent.name)
        event_logger.emit("agent_deployed", f"AGENT DEPLOYED: {agent.name} (auto)")

    if deployed_list:
        return f"AUTO-DEPLOYED: " + ", ".join(deployed_list) + f" [{player.get_deployed_count()}/{player.max_agent_slots} slots]"
    return ""

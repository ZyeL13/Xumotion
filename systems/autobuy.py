"""
Auto-enhance system - automated purchase logic for idle progression.
"""
from systems.economy import handle_upgrade, deploy_agent, get_upgrade_level
from game.registry import UPGRADE_REGISTRY, AGENT_REGISTRY, DEFAULT_AGENT_ID
from game.formulas import upgrade_cost


def autobuy_tick(state) -> list:
    player = state.player
    messages = []

    if not getattr(player, "auto_enhance", False):
        return messages

    # 1. Find cheapest upgrade
    cheapest = None
    cheapest_cost = float("inf")
    cheapest_key = None

    for key, upgrade in UPGRADE_REGISTRY.items():
        lvl = get_upgrade_level(player, key)
        cost = upgrade_cost(upgrade, lvl)
        if cost < cheapest_cost:
            cheapest_cost = cost
            cheapest = upgrade
            cheapest_key = key

    # 2. Buy cheapest upgrade while affordable
    while cheapest and player.gold >= cheapest_cost:
        msg = handle_upgrade(state, cheapest_key)
        messages.append(msg)
        lvl = get_upgrade_level(player, cheapest_key)
        cheapest_cost = upgrade_cost(cheapest, lvl)

    # 3. Deploy agent if affordable
    agent_def = AGENT_REGISTRY.get(DEFAULT_AGENT_ID)
    if agent_def:
        num_owned = sum(1 for a in player.agents if a.name.startswith(agent_def.name))
        from game.formulas import pet_cost
        cost = pet_cost(agent_def, num_owned)
        while player.gold >= cost and cost > 0:
            msg = deploy_agent(state)
            messages.append(msg)
            num_owned += 1
            cost = pet_cost(agent_def, num_owned)

    return messages

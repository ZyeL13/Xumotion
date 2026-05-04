def tick_automation(state):
    player = state.player
    total_dps = sum(agent.dps for agent in player.agents)
    player.dps = total_dps

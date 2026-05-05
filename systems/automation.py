def tick_automation(state):
    player = state.player
    total_dps = sum(agent.dps for agent in player.agents if agent.deployed)
    player.dps = total_dps

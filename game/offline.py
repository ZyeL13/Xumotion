import time
from game.constants import OFFLINE_PROGRESS_CAP
# earned_gold = offline_gold(player.dps, elapsed)

def calculate_offline_reward(state):
    player = state.player
    last_save = state.last_save
    now = time.time()
    elapsed = now - last_save

    if elapsed <= 0:
        return

    if OFFLINE_PROGRESS_CAP > 0 and elapsed > OFFLINE_PROGRESS_CAP:
        elapsed = OFFLINE_PROGRESS_CAP

    earned_gold = int(player.dps * elapsed)
    player.gold += earned_gold

    state.offline_message = (
        f"Offline for {elapsed:.0f}s. Earned {earned_gold} gold."
        + (" (capped)" if elapsed == OFFLINE_PROGRESS_CAP else "")
    )

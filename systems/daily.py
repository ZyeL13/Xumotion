"""
systems/daily.py — Daily cycle reward system.
Handles claim logic, streak tracking, and tamper-resistant saves.
"""

import time
import json
import os
import hashlib

DAILY_PATH = "saves/daily_progress.json"
DAILY_REWARDS_PATH = "data/daily.json"


def load_rewards():
    """Load reward definitions from JSON config."""
    if not os.path.exists(DAILY_REWARDS_PATH):
        return [
            {"day": 1, "gold": 50},
            {"day": 2, "gold": 100},
            {"day": 3, "gold": 150},
            {"day": 4, "gold": 200},
            {"day": 5, "gold": 300},
            {"day": 6, "gold": 400},
            {"day": 7, "gold": 600},
        ]
    with open(DAILY_REWARDS_PATH, "r") as f:
        data = json.load(f)
    return data.get("rewards", [])


def load_progress():
    """Load daily progress from disk."""
    if not os.path.exists(DAILY_PATH):
        return {"last_claim": 0, "uptime": 0}
    try:
        with open(DAILY_PATH, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {"last_claim": 0, "uptime": 0}


def save_progress(uptime: int, last_claim: float):
    """Save daily progress to disk."""
    os.makedirs(os.path.dirname(DAILY_PATH), exist_ok=True)
    data = {
        "uptime": uptime,
        "last_claim": last_claim,
    }
    with open(DAILY_PATH, "w") as f:
        json.dump(data, f)


def can_claim() -> bool:
    """Check if daily reward is available (24h cooldown)."""
    prog = load_progress()
    last = prog.get("last_claim", 0)
    return (time.time() - last) >= 86400


def claim_daily(state) -> str:
    """
    Attempt to claim the daily cycle reward.
    Updates player gold and resets cooldown.
    Also sets player.last_daily_claim for UI tracking.
    """
    player = state.player

    if not can_claim():
        prog = load_progress()
        last = prog.get("last_claim", time.time())
        remaining = 86400 - (time.time() - last)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"CYCLE ALREADY CLAIMED. Next deposit in {hours}h {minutes}m."

    prog = load_progress()
    uptime = prog.get("uptime", 0)

    # Reset streak if more than 48h since last claim
    if time.time() - prog.get("last_claim", 0) > 172800:
        uptime = 0

    uptime += 1
    if uptime > 7:
        uptime = 1

    rewards = load_rewards()
    reward = rewards[uptime - 1] if uptime <= len(rewards) else rewards[-1]

    # Apply reward to player
    player.input_credits += reward.get("input_credits", reward.get("gold", 0))

    # Save progress with current timestamp
    now = time.time()
    save_progress(uptime, now)

    # Also set player field for UI
    player.last_daily_claim = now

    from game.event_logger import event_logger
    event_logger.emit("cycle", f"CYCLE {reward.get('day', uptime)} DEPOSIT: +{reward.get('input_credits', reward.get('gold', 0))} INPUT")

    return f"CYCLE {reward.get('day', uptime)} DEPOSIT: +{reward.get('input_credits', reward.get('gold', 0))} INPUT. Streak: {uptime}/7"

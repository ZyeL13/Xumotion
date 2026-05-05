"""
Cycle rewards system - periodic credit deposits (tamper-resistant).
"""
import json
import time
import hashlib
from pathlib import Path

DAILY_DATA = Path(__file__).parent.parent / "data" / "daily.json"
DAILY_SAVE = Path(__file__).parent.parent / "saves" / "daily.json"
DAILY_SALT = "xumotion_daily_v1"


def _checksum(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True) + DAILY_SALT
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_rewards() -> list:
    with open(DAILY_DATA, "r") as f:
        return json.load(f).get("rewards", [])


def load_progress() -> dict:
    if DAILY_SAVE.exists():
        with open(DAILY_SAVE, "r") as f:
            try:
                saved = json.load(f)
            except Exception:
                return {"uptime": 0, "last_claim": 0}
        data = saved.get("data", {})
        checksum_val = saved.get("checksum", "")
        if checksum_val != _checksum(data):
            # Tampering detected — reset progress
            return {"uptime": 0, "last_claim": 0}
        return data
    return {"uptime": 0, "last_claim": 0}


def save_progress(uptime: int, last_claim: float):
    DAILY_SAVE.parent.mkdir(parents=True, exist_ok=True)
    data = {"uptime": uptime, "last_claim": last_claim}
    chk = _checksum(data)
    with open(DAILY_SAVE, "w") as f:
        json.dump({"data": data, "checksum": chk}, f, indent=2)


def can_claim() -> bool:
    prog = load_progress()
    last = prog.get("last_claim", 0)
    now = time.time()
    return (now - last) >= 86400


def claim_daily(state) -> str:
    if not can_claim():
        prog = load_progress()
        last = prog.get("last_claim", time.time())
        remaining = 86400 - (time.time() - last)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"CYCLE ALREADY CLAIMED. Next deposit in {hours}h {minutes}m."

    prog = load_progress()
    uptime = prog.get("uptime", 0)

    if time.time() - prog.get("last_claim", 0) > 172800:
        uptime = 0

    uptime += 1
    if uptime > 7:
        uptime = 1

    rewards = load_rewards()
    reward = rewards[uptime - 1]

    player = state.player
    player.gold += reward["gold"]

    save_progress(uptime, time.time())

    from game.event_logger import event_logger
    event_logger.emit("cycle", f"CYCLE {reward['day']} DEPOSIT: +{reward['gold']} CREDITS")

    return f"CYCLE {reward['day']} DEPOSIT: +{reward['gold']} CREDITS. Uptime: {uptime} day(s)."

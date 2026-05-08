"""
Log tracker - load/save/check log entries.
"""
import json
from pathlib import Path
from game.event_logger import event_logger

ACH_DATA = Path(__file__).parent.parent / "data" / "achievements.json"
ACH_SAVE = Path(__file__).parent.parent / "saves" / "achievements.json"


def load_definitions() -> list:
    with open(ACH_DATA, "r") as f:
        data = json.load(f)
    return data.get("achievements", [])


def load_progress() -> dict:
    if ACH_SAVE.exists():
        with open(ACH_SAVE, "r") as f:
            return json.load(f)
    return {"completed": []}


def save_progress(completed: list):
    ACH_SAVE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACH_SAVE, "w") as f:
        json.dump({"completed": completed}, f, indent=2)


def check_and_unlock(state) -> list:
    definitions = load_definitions()
    progress = load_progress()
    completed = set(progress.get("completed", []))
    newly_unlocked = []

    p = state.player
    stats = {
        "kills": state.kills_in_stage,
        "stage": state.sector * 10 + state.substage,
        "credits": p.gold,
        "rank": p.level,
        "recompile": p.recompile_count,
    }

    for ach in definitions:
        if ach["id"] in completed:
            continue
        current = stats.get(ach["type"], 0)
        if current >= ach["target"]:
            completed.add(ach["id"])
            newly_unlocked.append(ach)
            p.gold += ach.get("reward_credits", 0)
            event_logger.emit("log_entry", f"LOG ENTRY: {ach['name']} (+{ach['reward_credits']} CREDITS)")

    if newly_unlocked:
        save_progress(list(completed))

    return newly_unlocked

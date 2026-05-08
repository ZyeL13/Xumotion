import time
from game.state import GameState
from game.save_manager import save_game
from game.combat import tick_combat
from systems.automation import tick_automation
from game.event_logger import event_logger
from systems.autobuy import autobuy_tick
from game.constants import PRESTIGE_STAGE_REQ
from systems.economy import handle_upgrade, enhance_agent
from systems.modules import auto_install_best, install_module, uninstall_slot
from systems.prestige import can_prestige, get_core_gain
from systems.daily import claim_daily, can_claim, load_progress
from game.achievement_tracker import load_definitions as load_ach_defs
from game.achievement_tracker import load_progress as load_ach_prog

def _validate_command_input(cmd: str) -> tuple:
    """Return (is_valid, error_message)."""
    if not cmd:
        return False, "Empty command"
    if len(cmd) > 500:
        return False, "Command too long"
    # Hanya izinkan karakter alfanumerik, spasi, strip, underscore, slash
    if not all(c.isalnum() or c in ' -_/#' for c in cmd):
        return False, "Invalid characters"
    parts = cmd.strip().lower().split()
    if len(parts) > 10:
        return False, "Too many arguments"
    return True, ""

def process_command(state: GameState, cmd: str) -> str:
    """Process a command (thread-safe). Returns response string."""
    if not cmd.strip():
        return ""

    with state.lock:
        cmd_clean = cmd.strip().lower()
        valid, err = _validate_command_input(cmd_clean)
        if not valid:
            return f"COMMAND REJECTED: {err}"
        shortcut_map = {
            "1": "enhance atk",
            "2": "enhance defense",
            "3": "enhance max_hp",
            "4": "enhance crit_rate",
            "5": "deploy agent",
            "6": "stats",
            "7": "checkpoint",
            "8": "shutdown",
            "9": "recompile",
        }
        if cmd_clean in shortcut_map:
            cmd_clean = shortcut_map[cmd_clean]

        parts = cmd_clean.split()
        if not parts:
            return ""

        action = parts[0]
        player = state.player

        if action == "stats":
            return f"RANK {player.level} | CREDITS: {player.gold} | ATK: {player.atk} | DPS: {player.dps} | DEF: {player.defense}"

        elif action in ("enhance", "upgrade", "up"):
            if len(parts) < 2:
                return "USAGE: enhance <atk|defense|max_hp|crit_rate>"
            return handle_upgrade(state, parts[1])

        elif action in ("deploy", "buy", "b"):
            from systems.economy import deploy_agent, deploy_specific_agent
            from game.registry import AGENT_REGISTRY
            if len(parts) < 2 or parts[1] in ("agent", "agents"):
                return deploy_agent(state)  # beli agent termurah (auto-deploy kalau ada slot)
            elif parts[1] == "list":
                lines = ["AVAILABLE AGENTS:"]
                for agent_id, agent_def in AGENT_REGISTRY.items():
                    owned = sum(1 for a in player.agents if a.name.startswith(agent_def.name))
                    from game.formulas import pet_cost
                    cost = pet_cost(agent_def, owned)
                    lines.append(f"  {agent_def.name} (Tier: {agent_def.tier}, DPS {agent_def.base_dps}) — {cost} credits")
                return "\n".join(lines)
            else:
                # Mencoba memasang agent yang sudah dimiliki (dari bay) ke slot
                return deploy_specific_agent(state, parts[1])

        elif action in ("undeploy", "uns"):
            if len(parts) < 2:
                return "USAGE: undeploy <agent name/number>"
            from systems.economy import undeploy_agent
            return undeploy_agent(state, parts[1])

        elif action in ("merge",):
            # Format baru: merge <unit_name> <slot1> <slot2> <slot3>  -> 5 token
            # Format lama: merge <slot1> <slot2> <slot3>              -> 4 token
            if len(parts) == 4:
                # Format lama (hanya angka slot, tanpa nama)
                from systems.economy import merge_agents
                return merge_agents(state, None, parts[1], parts[2], parts[3])
            elif len(parts) == 5:
                unit_name = parts[1]  # "echo" → nanti dicocokkan dengan "Echo Unit"
                slot1, slot2, slot3 = parts[2], parts[3], parts[4]
                from systems.economy import merge_agents
                return merge_agents(state, unit_name, slot1, slot2, slot3)
            else:
                return "USAGE: merge <unit_name> <slot1> <slot2> <slot3>\nExample: merge Echo 1 2 3"

        elif action in ("install", "equip", "eq"):
            if len(parts) < 2:
                return auto_install_best(state)
            try:
                index = int(parts[1])
                return install_module(player, index)
            except ValueError:
                return "USAGE: /install (auto) or /install <bay number>"

        elif action in ("uninstall", "unequip", "uneq"):
            if len(parts) < 2:
                return "USAGE: uninstall <injector|barrier|cache>"
            return uninstall_slot(player, parts[1])

        elif action in ("core", "pp"):
            core_total = player.core_points
            if can_prestige(state):
                gain = get_core_gain(state)
                return f"CORE: {core_total} | READY! +{gain} CORE on recompile."
            else:
                need = PRESTIGE_STAGE_REQ - state.sector
                return f"CORE: {core_total} | Need Sector {PRESTIGE_STAGE_REQ} (current: {state.sector}, {need} more)"

        elif action in ("next",):
            if state.boss_active:
                # Restart boss fight
                from models.enemy import Enemy
                state.enemy = Enemy.generate(state.sector, state.substage, state.player)
                # Reset timer sesuai sektor
                if state.sector <= 5:
                    state.boss_timer = 60.0
                elif state.sector <= 15:
                    state.boss_timer = 45.0
                else:
                    state.boss_timer = 30.0
                event_logger.emit("boss_retry", f"BOSS RETRY — Sector {state.sector} · 10/10")
                return f"BOSS RETRY — Sector {state.sector} · 10/10. Timer started."
            else:
                return "No active boss to retry."

        elif action in ("recompile", "prestige", "rebirth"):
            from systems.prestige import do_prestige
            return do_prestige(state)

        elif action in ("auto", "autobuy"):
            if len(parts) > 1 and parts[1] in ("on", "enable", "start"):
                player.auto_enhance = True
                return "AUTO-ENHANCE ENABLED."
            elif len(parts) > 1 and parts[1] in ("off", "disable", "stop"):
                player.auto_enhance = False
                return "AUTO-ENHANCE DISABLED."
            else:
                status = "ON" if getattr(player, "auto_enhance", False) else "OFF"
                return f"Auto-enhance is {status}. Usage: auto on/off"

        elif action in ("cycle", "daily", "claim"):
            if not can_claim():
                import time as time_mod
                prog = load_progress()
                last = prog.get("last_claim", time_mod.time())
                remaining = 86400 - (time_mod.time() - last)
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return f"Next cycle in {hours}h {minutes}m."
            return claim_daily(state)

        elif action in ("modules", "inv", "inventory", "i"):
            agents_str = ", ".join(a.name for a in player.agents) if player.agents else "none"
            bay_count = len(player.inventory)
            if bay_count == 0:
                bay_str = "empty"
            else:
                items = []
                for mod in player.inventory:
                    status = " [INSTALLED]" if mod.installed else ""
                    items.append(f"{mod.name} ({mod.rarity.value}){status}")
                bay_str = ", ".join(items)
            return f"AGENTS: {agents_str} | MODULE BAY ({bay_count}): {bay_str}"

        elif action in ("log", "ach", "achievements"):
            defs = load_ach_defs()
            prog = load_ach_prog()
            completed = set(prog.get("completed", []))
            total = len(defs)
            unlocked = len(completed)
            lines = [f"LOG ENTRIES: {unlocked}/{total}"]
            for ach in defs:
                mark = "OK" if ach["id"] in completed else "--"
                lines.append(f"{mark} {ach['name']} - {ach['desc']}")
            return "\n".join(lines)

        elif action in ("checkpoint", "save", "s"):
            save_game(state)
            return "CHECKPOINT SAVED."

        elif action in ("shutdown", "quit", "q", "exit"):
            state.running = False
            return "SHUTTING DOWN..."

        elif action in ("enhance_agent", "ea"):
            if len(parts) < 2:
                return "USAGE: /ea <agent name>"
            return enhance_agent(state, parts[1])

        elif action in ("help", "h", "?"):
            return "enhance <stat> | deploy agent | install <n> | uninstall <slot> | recompile | core | auto | cycle | log | modules | restore | checkpoint | shutdown | ea <agent> | merge <id1> <id2> <id3>"

        else:
            return f"UNKNOWN: '{action}'. Type 'help' for commands."


def game_loop(state: GameState):
    last_tick = time.time()
    tick_rate = 1.0

    while state.running:
        now = time.time()
        delta = now - last_tick

        if delta >= tick_rate:
            print("[LOOP] Acquiring lock...")
            with state.lock:
                print("[LOOP] Lock acquired. Ticking...")
                tick_combat(state)
                tick_automation(state)
                msgs = autobuy_tick(state)
                for msg in msgs:
                    event_logger.emit("auto_enhance", msg)
                save_game(state)
                print("[LOOP] Tick done. Releasing lock.")
            last_tick = now

        time.sleep(0.1)

    print("[LOOP] Exiting game loop.")
    save_game(state)

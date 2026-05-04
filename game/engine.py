import time
import threading
from game.state import GameState
from game.save_manager import save_game, load_game
from game.combat import tick_combat
from systems.automation import tick_automation
from game.event_logger import event_logger
from systems.autobuy import autobuy_tick


def process_command(state: GameState, cmd: str) -> str:
    """Process a command (thread-safe). Returns response string."""
    if not cmd.strip():
        return ""

    with state.lock:
        cmd_clean = cmd.strip().lower()
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
            from systems.economy import handle_upgrade
            return handle_upgrade(state, parts[1])

        elif action in ("deploy", "buy", "b"):
            from systems.economy import deploy_agent
            from game.registry import AGENT_REGISTRY
            if len(parts) < 2 or parts[1] in ("agent", "agents"):
                return deploy_agent(state)
            elif parts[1] == "list":
                lines = ["AVAILABLE AGENTS:"]
                for agent_id, agent_def in AGENT_REGISTRY.items():
                    owned = sum(1 for a in player.agents if a.name.startswith(agent_def.name))
                    from game.formulas import pet_cost
                    cost = pet_cost(agent_def, owned)
                    lines.append(f"  {agent_def.name} (DPS {agent_def.base_dps}) — {cost} credits")
                return "\n".join(lines)
            else:
                return deploy_agent(state, parts[1])

        elif action in ("install", "equip", "eq"):
            if len(parts) < 2:
                from systems.modules import auto_install_best
                return auto_install_best(player)
            try:
                index = int(parts[1])
                from systems.modules import install_module
                return install_module(player, index)
            except ValueError:
                return "USAGE: /install (auto) or /install <bay number>"
        elif action in ("uninstall", "unequip", "uneq"):
            if len(parts) < 2:
                return "USAGE: uninstall <injector|barrier|cache>"
            from systems.modules import uninstall_slot
            return uninstall_slot(player, parts[1])
        elif action in ("core", "pp"):
            from game.constants import PRESTIGE_STAGE_REQ
            from systems.prestige import can_prestige, get_core_gain
            core_total = player.core_points
            can = can_prestige(state)
            if can:
                gain = get_core_gain(state)
                return f"CORE: {core_total} | READY! +{gain} CORE on recompile."
            else:
                need = PRESTIGE_STAGE_REQ - state.current_stage
                return f"CORE: {core_total} | Need Sector {PRESTIGE_STAGE_REQ} (current: {state.current_stage}, {need} more)"
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
            from systems.daily import claim_daily, can_claim
            if not can_claim():
                import time as time_mod
                from systems.daily import load_progress
                prog = load_progress()
                last = prog.get("last_claim", time_mod.time())
                remaining = 86400 - (time_mod.time() - last)
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return f"Next cycle in {hours}h {minutes}m."
            return claim_daily(state)
        elif action in ("die", "killme"):
            player.hp = 0
            state.player_dead = True
            event_logger.emit("player_died", "OPERATOR DOWN — Type /restore to continue")
            return "OPERATOR DOWN. Type /restore to continue."
        elif action in ("restore", "revive", "next"):
            if getattr(state, "player_dead", False):
                player.hp = player.effective_max_hp
                state.player_dead = False
                state.current_stage += 1
                from models.enemy import Enemy
                state.enemy = Enemy.generate(state.current_stage)
                event_logger.emit("restore", f"OPERATOR RESTORED — Sector {state.current_stage}")
                return f"OPERATOR RESTORED. Sector {state.current_stage}."
            return "Operator is active. No restoration needed."
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
            from game.achievement_tracker import load_definitions, load_progress
            defs = load_definitions()
            prog = load_progress()
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
            from systems.economy import enhance_agent
            return enhance_agent(state, parts[1])
        elif action in ("help", "h", "?"):
            return "enhance <stat> | deploy agent | install <n> | uninstall <slot> | recompile | core | auto | cycle | log | modules | restore | checkpoint | shutdown | ea <agent>"
        else:
            return f"UNKNOWN: '{action}'. Type 'help' for commands."


def game_loop(state: GameState):
    """Blocking game loop (call in separate thread)."""
    last_tick = time.time()
    tick_rate = 1.0

    while state.running:
        now = time.time()
        delta = now - last_tick

        if delta >= tick_rate:
            with state.lock:
                tick_combat(state)
                tick_automation(state)
                msgs = autobuy_tick(state)
                for msg in msgs:
                    event_logger.emit("auto_enhance", msg)
                save_game(state)
            last_tick = now

        time.sleep(0.1)

    save_game(state)

import sys
import shutil
import time
from rich.console import Console
from rich.table import Table
from rich import box
from game.state import GameState
from game.event_logger import event_logger

console = Console()
_event_history = []


def render_game_area(state: GameState):
    global _event_history

    sys.stdout.write('\033[H')
    player = state.player
    enemy = state.enemy

    table = Table(title="SYSTEMS INTERFACE", box=box.SIMPLE_HEAVY, title_style="bold cyan", min_width=50)
    table.add_column("Property", style="cyan", no_wrap=True, min_width=12)
    table.add_column("Value", style="green", no_wrap=True)

    table.add_row("Sector", str(state.current_stage))
    table.add_row("Entity", f"{enemy.name} ({enemy.rarity})")
    hp_percent = max(0, enemy.hp) / enemy.max_hp if enemy.max_hp > 0 else 0
    hp_color = "green" if hp_percent > 0.5 else "yellow" if hp_percent > 0.25 else "red"
    table.add_row("Integrity", f"[{hp_color}]{max(0, enemy.hp)}/{enemy.max_hp}[/{hp_color}]")

    table.add_section()
    table.add_row("Credits", f"[bold yellow]{player.gold}[/bold yellow]")
    table.add_row("Rank", str(player.level))
    try:
        from systems.progression import required_exp
        exp_needed = required_exp(player.level)
        table.add_row("EXP", f"{player.exp}/{exp_needed}")
    except Exception:
        table.add_row("EXP", f"{player.exp}/?")

    table.add_row("ATK", str(player.atk))
    table.add_row("DPS", str(player.dps))
    table.add_row("DEF", str(player.defense))
    table.add_row("CRIT", f"{player.crit_rate:.2%} x{player.crit_damage:.1f}")
    table.add_row("Integrity", f"{player.hp}/{player.max_hp}")

    agents_str = ", ".join(a.name for a in player.agents) if player.agents else "none"
    table.add_row("Agents", agents_str)

    bay_count = len(player.inventory)
    table.add_row("Module Bay", f"{bay_count} modules" if bay_count else "empty")

    console.print(table)

    while True:
        ev = event_logger.poll()
        if ev is None:
            break
        _event_history.append(ev)

    if len(_event_history) > 10:
        _event_history = _event_history[-10:]

    console.print("─" * 50)
    console.print("[bold cyan]EVENT LOG:[/bold cyan]")
    for ev in _event_history:
        ts = time.strftime("%H:%M:%S", time.localtime(ev.timestamp))
        msg = ev.message[:80] + "..." if len(ev.message) > 80 else ev.message
        console.print(f"[dim]{ts}[/dim] {msg}")

    sys.stdout.write('\033[J')
    sys.stdout.flush()


def monitor_loop(state: GameState):
    sys.stdout.write('\033[?1049h')
    sys.stdout.write('\033[2J')
    try:
        while state.running:
            with state.lock:
                render_game_area(state)
            time.sleep(1.0)
    finally:
        sys.stdout.write('\033[?1049l')
        print("Monitor terminated.")

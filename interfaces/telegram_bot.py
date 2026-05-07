"""
telegram_bot.py — Telegram interface for the XUMOTION RPG bot.

Responsibilities:
  - Expose game state via reply keyboard UI
  - Route keyboard button presses to game engine commands
  - Manage per-user session state (screen, awaiting-input mode)
  - Handle slash commands as fallback/power-user path

Session dict shape: {"mode": str | None, "screen": str}
"""
import os
import asyncio
from telegram import Update, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from game.engine import process_command
from game.state import GameState
from game.event_logger import event_logger
from systems.progression import required_exp

TELEGRAM_TOKEN = os.environ.get("RPG_BOT_TOKEN", "")
ADMIN_IDS_STR = os.environ.get("TELEGRAM_ADMIN_IDS", "")
ADMIN_IDS = set(ADMIN_IDS_STR.split(",")) if ADMIN_IDS_STR else set()

# Session per user
user_sessions = {}


def _is_authorized(update: Update) -> bool:
    if not ADMIN_IDS:
        return True
    return str(update.effective_user.id) in ADMIN_IDS


def _build_main_keyboard() -> ReplyKeyboardMarkup:
    """Return the top-level navigation keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Status"), KeyboardButton("Agent")],
            [KeyboardButton("Module"), KeyboardButton("Upgrade")],
            [KeyboardButton("Progress"), KeyboardButton("System")],
            [KeyboardButton("Help")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=False
    )


def _build_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard shown while awaiting user text input."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Cancel"), KeyboardButton("Back")]],
        resize_keyboard=True,
    )


class TelegramBot:
    def __init__(self, state: GameState):
        self.state = state
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self._register_handlers()

    def _format_stats(self) -> str:
        """Build the main dashboard text block (sector, enemy HP, operator stats)."""
        p = self.state.player
        e = self.state.enemy
        try:
            exp_needed = required_exp(p.level)
        except Exception:
            exp_needed = "?"

        hp_current = max(0, e.hp)
        hp_pct = hp_current / e.max_hp if e.max_hp > 0 else 0
        hp_bar = "█" * int(hp_pct * 10) + "░" * (10 - int(hp_pct * 10))

        exp_now = p.exp
        exp_need = exp_needed if isinstance(exp_needed, int) and exp_needed > 0 else 1
        xp_pct = min(exp_now / exp_need, 1.0)
        xp_bar = "█" * int(xp_pct * 10) + "░" * (10 - int(xp_pct * 10))

        agents_active = len(p.agents)
        agents_str = f"{agents_active} ACTIVE" if agents_active > 0 else "NONE"

        zone_map = {
            (0, 9): "SANDBOX", (10, 19): "RELAY BASIN", (20, 29): "COLD STORAGE",
            (30, 39): "MIRROR SECTOR", (40, 49): "ARCHIVE LAYER", (50, 59): "NULL ZONE",
            (60, 69): "SIGNAL DEPTHS", (70, 79): "CORE NETWORK", (80, 89): "ECHO VOID",
            (90, 99): "GENESIS RING",
        }
        stage = self.state.current_stage
        zone = "UNKNOWN"
        for (lo, hi), name in zone_map.items():
            if lo <= stage <= hi:
                zone = name
                break
        if stage > 99:
            zone = "DEEP LAYER"

        log_msg = ""
        ev = event_logger.poll()
        if ev:
            log_msg = ev.message[:40]

        lines = [
            "SYSTEM ONLINE",
            "",
            f"SECTOR {stage} - {zone}",
            f"{e.name} [{e.rarity.upper()}]",
            f"INTEGRITY {hp_bar} {hp_current}/{e.max_hp}",
            "",
            "OPERATOR",
            f"Credits: {p.gold}",
            f"Rank: {p.level}       EXP {xp_bar} {exp_now}/{exp_needed}",
            f"ATK: {p.atk}             DPS: {p.dps}",
            f"DEF: {p.defense}            CRIT: {p.crit_rate:.0%} x{p.crit_damage:.1f}",
            f"Integrity: {p.hp}/{p.effective_max_hp}",
            f"Agents: {agents_str} [{p.get_deployed_count()}/{p.max_agent_slots} slots]",
        ]

        if log_msg:
            lines.append(f"LOG: {log_msg}")

        return "\n".join(lines)

    async def _set_bot_commands(self):
        commands = [
            BotCommand("start", "Main menu"),
            BotCommand("cancel", "Cancel current operation"),
        ]
        await self.app.bot.set_my_commands(commands)

    def _register_handlers(self):
        """Define and register all command + text message handlers as closures.

        Closures share access to `self.state` and `user_sessions` via enclosing
        scope. All navigation handlers follow the same pattern:
          1. Set session screen
          2. Send menu text + sub-keyboard
        """
        # --- Main /start ---
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            user_sessions[user_id] = {"mode": None, "screen": "main_menu"}
            await update.message.reply_text("SYSTEM ONLINE\n\n" + self._format_stats(),
                                            reply_markup=_build_main_keyboard())

        # --- /status ---
        async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            prev = user_sessions.get(user_id, {}).get("screen", "main_menu")
            user_sessions[user_id] = {"mode": None, "screen": "status", "prev_screen": prev}
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("Stats"), KeyboardButton("Core")],
                    [KeyboardButton("Back")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False
            )
            await update.message.reply_text("STATUS MENU", reply_markup=keyboard)

        # --- /agent ---
        async def agent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            prev = user_sessions.get(user_id, {}).get("screen", "main_menu")
            user_sessions[user_id] = {"mode": None, "screen": "agent", "prev_screen": prev}
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("List Agents"), KeyboardButton("Deploy")],
                    [KeyboardButton("Undeploy"), KeyboardButton("Merge")],
                    [KeyboardButton("Enhance Agent")],
                    [KeyboardButton("Back")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False
            )
            await update.message.reply_text("AGENT MENU", reply_markup=keyboard)

        # --- /module ---
        async def module_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            prev = user_sessions.get(user_id, {}).get("screen", "main_menu")
            user_sessions[user_id] = {"mode": None, "screen": "module", "prev_screen": prev}
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("List Modules"), KeyboardButton("Install")],
                    [KeyboardButton("Uninstall")],
                    [KeyboardButton("Back")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False
            )
            await update.message.reply_text("MODULE MENU", reply_markup=keyboard)

        # --- /upgrade ---
        async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            prev = user_sessions.get(user_id, {}).get("screen", "main_menu")
            user_sessions[user_id] = {"mode": None, "screen": "upgrade", "prev_screen": prev}
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("Upgrade ATK"), KeyboardButton("Upgrade DEF")],
                    [KeyboardButton("Upgrade HP"), KeyboardButton("Upgrade CRIT")],
                    [KeyboardButton("Back")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False
            )
            await update.message.reply_text("UPGRADE MENU", reply_markup=keyboard)

        # --- /progress ---
        async def progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            prev = user_sessions.get(user_id, {}).get("screen", "main_menu")
            user_sessions[user_id] = {"mode": None, "screen": "progress", "prev_screen": prev}
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("Checkpoint"), KeyboardButton("Restore")],
                    [KeyboardButton("Recompile")],
                    [KeyboardButton("Back")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False
            )
            await update.message.reply_text("PROGRESS MENU", reply_markup=keyboard)

        # --- /system ---
        async def system_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            prev = user_sessions.get(user_id, {}).get("screen", "main_menu")
            user_sessions[user_id] = {"mode": None, "screen": "system", "prev_screen": prev}
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("Auto"), KeyboardButton("Cycle")],
                    [KeyboardButton("Log"), KeyboardButton("Save")],
                    [KeyboardButton("Back")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False
            )
            await update.message.reply_text("SYSTEM MENU", reply_markup=keyboard)

        # --- /help ---
        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = (
                "📋 XUMOTION — SYSTEMS CONSOLE\n\n"
                "Gunakan tombol di keyboard bawah untuk navigasi.\n\n"
                "Status   : Cek status operator & core\n"
                "Agent    : Kelola agen (deploy/undeploy/merge/enhance)\n"
                "Module   : Kelola modul (list/install/uninstall)\n"
                "Upgrade  : Tingkatkan ATK/DEF/HP/CRIT\n"
                "Progress : Cek sektor, checkpoint, restore, recompile\n"
                "System   : Auto, cycle, log, save\n\n"
                "/start   : Tampilkan dashboard & keyboard utama\n"
                "/cancel  : Batalkan operasi yang sedang berjalan"
            )
            await update.message.reply_text(text, reply_markup=_build_main_keyboard())

        # --- /cancel ---
        async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            user_sessions[user_id] = {"mode": None, "screen": "main_menu"}
            await update.message.reply_text("Operation cancelled.", reply_markup=_build_main_keyboard())

        # --- Text handler for input mode & keyboard buttons ---
        async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            session = user_sessions.get(user_id)
            if session is None:
                session = {"mode": None, "screen": "main_menu"}
                user_sessions[user_id] = session
            text = update.message.text.strip()
            print(f"[DEBUG] user={user_id} text='{text}' screen={session.get('screen') if session else 'None'}")

            # Always handle Back/Cancel immediately
            if text == "Back":
                was_in_mode = bool(session.get("mode"))
                session["mode"] = None

                if was_in_mode:
                    # User menekan Back saat awaiting input (e.g. setelah pencet Install).
                    # Kembali ke sub-menu saat ini, bukan prev_screen.
                    target = session.get("screen", "main_menu")
                else:
                    # User menekan Back dari sub-menu biasa → naik satu level.
                    target = session.pop("prev_screen", "main_menu")
                    session["screen"] = target

                _sub_keyboards = {
                    "status":   (
                        "STATUS MENU",
                        [[KeyboardButton("Stats"), KeyboardButton("Core")],
                         [KeyboardButton("Back")]],
                    ),
                    "agent":    (
                        "AGENT MENU",
                        [[KeyboardButton("List Agents"), KeyboardButton("Deploy")],
                         [KeyboardButton("Undeploy"), KeyboardButton("Merge")],
                         [KeyboardButton("Enhance Agent")],
                         [KeyboardButton("Back")]],
                    ),
                    "module":   (
                        "MODULE MENU",
                        [[KeyboardButton("List Modules"), KeyboardButton("Install")],
                         [KeyboardButton("Uninstall")],
                         [KeyboardButton("Back")]],
                    ),
                    "upgrade":  (
                        "UPGRADE MENU",
                        [[KeyboardButton("Upgrade ATK"), KeyboardButton("Upgrade DEF")],
                         [KeyboardButton("Upgrade HP"), KeyboardButton("Upgrade CRIT")],
                         [KeyboardButton("Back")]],
                    ),
                    "progress": (
                        "PROGRESS MENU",
                        [[KeyboardButton("Checkpoint"), KeyboardButton("Restore")],
                         [KeyboardButton("Recompile")],
                         [KeyboardButton("Back")]],
                    ),
                    "system":   (
                        "SYSTEM MENU",
                        [[KeyboardButton("Auto"), KeyboardButton("Cycle")],
                         [KeyboardButton("Log"), KeyboardButton("Save")],
                         [KeyboardButton("Back")]],
                    ),
                }

                if target == "main_menu" or target not in _sub_keyboards:
                    await update.message.reply_text("Main Menu", reply_markup=_build_main_keyboard())
                else:
                    label, rows = _sub_keyboards[target]
                    kb = ReplyKeyboardMarkup(rows, resize_keyboard=True)
                    await update.message.reply_text(label, reply_markup=kb)
                return
            if text == "Cancel":
                session["mode"] = None
                await update.message.reply_text("Dibatalkan.", reply_markup=_build_main_keyboard())
                return

            # Route button presses according to current screen
            screen = session.get("screen", "main_menu")
            response = None

            try:
                # --- Main menu navigation buttons ---
                if screen == "main_menu":
                    _main_nav = {
                        "status": status_cmd, "agent": agent_cmd,
                        "module": module_cmd, "upgrade": upgrade_cmd,
                        "progress": progress_cmd, "system": system_cmd,
                        "help": help_cmd,
                    }
                    handler = _main_nav.get(text.lower())
                    if handler:
                        return await handler(update, context)

                elif screen == "status":
                    if text == "Stats":
                        data = process_command(self.state, "stats")
                        response = f"OPERATOR STATS\n\n{data}" if data else "No data"
                    elif text == "Core":
                        data = process_command(self.state, "core")
                        response = f"CORE STATUS\n\n{data}" if data else "No data"

                elif screen == "agent":
                    if text == "List Agents":
                        p = self.state.player
                        if not p.agents:
                            response = "No agents deployed."
                        else:
                            lines = ["AGENTS\n"]
                            for i, a in enumerate(p.agents, 1):
                                status = "ACTIVE" if a.deployed else "INACTIVE"
                                lines.append(f"[{i}] {a.name}")
                                lines.append(f"ID: `{a.id}`")
                                lines.append(f"{status} | {a.tier.capitalize()} | Lv.{a.level} | DPS {a.dps}")
                                lines.append("")
                            lines.append("Quick actions:")
                            lines.append("`/agent deploy 1`")
                            lines.append("`/agent enhance 2`")
                            lines.append("`/agent merge Echo 1 2 3`")
                            response = "\n".join(lines)
                            await update.message.reply_text(response, parse_mode="Markdown")
                            return

                    elif text == "Deploy":
                        session["mode"] = "awaiting_deploy"
                        await update.message.reply_text("Enter agent ID to deploy:",
                                                        reply_markup=_build_cancel_keyboard())
                        return

                    elif text == "Undeploy":
                        session["mode"] = "awaiting_undeploy"
                        await update.message.reply_text("Enter agent ID to undeploy:",
                                                        reply_markup=_build_cancel_keyboard())
                        return

                    elif text == "Merge":
                        session["mode"] = "awaiting_merge"
                        await update.message.reply_text("Enter agent IDs to merge (e.g. 1 2):",
                                                        reply_markup=_build_cancel_keyboard())
                        return

                    elif text == "Enhance Agent":
                        session["mode"] = "awaiting_enhance"
                        await update.message.reply_text("Enter agent ID to enhance:",
                                                        reply_markup=_build_cancel_keyboard())
                        return

                elif screen == "module":
                    if text == "List Modules":
                        data = process_command(self.state, "modules")
                        response = f"MODULE BAY & AGENTS\n\n{data}" if data else "No data"
                    elif text == "Install":
                        session["mode"] = "awaiting_module_install"
                        await update.message.reply_text("Enter module ID to install (or leave empty for auto):",
                                                        reply_markup=_build_cancel_keyboard())
                        return

                    elif text == "Uninstall":
                        session["mode"] = "awaiting_module_uninstall"
                        await update.message.reply_text("Enter module ID to uninstall:",
                                                        reply_markup=_build_cancel_keyboard())
                        return

                elif screen == "upgrade":
                    if text == "Upgrade ATK":
                        response = process_command(self.state, "enhance atk")
                    elif text == "Upgrade DEF":
                        response = process_command(self.state, "enhance defense")
                    elif text == "Upgrade HP":
                        response = process_command(self.state, "enhance max_hp")
                    elif text == "Upgrade CRIT":
                        response = process_command(self.state, "enhance crit_rate")

                elif screen == "progress":
                    if text == "Checkpoint":
                        response = process_command(self.state, "checkpoint")
                    elif text == "Restore":
                        response = process_command(self.state, "restore")
                    elif text == "Recompile":
                        response = process_command(self.state, "recompile")

                elif screen == "system":
                    if text == "Auto":
                        response = process_command(self.state, "auto")
                    elif text == "Cycle":
                        response = process_command(self.state, "cycle")
                    elif text == "Log":
                        response = process_command(self.state, "log")
                    elif text == "Save":
                        response = process_command(self.state, "checkpoint")

                if response:
                    await update.message.reply_text(response)
                    return

                # --- Mode input (awaiting text from user after a button prompt) ---
                if session.get("mode"):
                    mode = session["mode"]
                    result = None

                    _mode_dispatch = {
                        "awaiting_deploy":           lambda t: f"deploy {t}",
                        "awaiting_undeploy":         lambda t: f"undeploy {t}",
                        "awaiting_enhance":          lambda t: f"ea {t}",
                        "awaiting_module_uninstall": lambda t: f"uninstall {t}",
                    }
                    if mode in _mode_dispatch:
                        result = process_command(self.state, _mode_dispatch[mode](text))
                    elif mode == "awaiting_merge":
                        result = process_command(self.state, f"merge {text}")
                    elif mode == "awaiting_module_install":
                        cmd = f"install {text}" if text.isdigit() else "install"
                        result = process_command(self.state, cmd)

                    if result:
                        await update.message.reply_text(result)
                    session["mode"] = None
                    await update.message.reply_text("Selesai.", reply_markup=_build_main_keyboard())

            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")
                print(f"[ERROR] {e}")

        # --- Registrasi semua handler ---
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(CommandHandler("status", status_cmd))
        self.app.add_handler(CommandHandler("agent", agent_cmd))
        self.app.add_handler(CommandHandler("module", module_cmd))
        self.app.add_handler(CommandHandler("upgrade", upgrade_cmd))
        self.app.add_handler(CommandHandler("progress", progress_cmd))
        self.app.add_handler(CommandHandler("system", system_cmd))
        self.app.add_handler(CommandHandler("help", help_cmd))
        self.app.add_handler(CommandHandler("cancel", cancel_cmd))

        # Handler untuk input teks biasa (mode input & tombol keyboard)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    async def run(self):
        if not TELEGRAM_TOKEN:
            print("TELEGRAM_BOT_TOKEN not set. Bot not started.")
            return
        await self.app.initialize()
        await self.app.start()
        await self._set_bot_commands()
        await self.app.updater.start_polling()
        print("Telegram bot started...")
        try:
            while self.state.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass  # abaikan
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            print("Bot stopped.")

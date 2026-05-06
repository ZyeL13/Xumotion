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

def _build_main_keyboard():
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

class TelegramBot:
    def __init__(self, state: GameState):
        self.state = state
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self._register_handlers()

    def _format_stats(self) -> str:
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
        # --- Main /start ---
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            user_sessions[user_id] = {"mode": None, "screen": "main_menu"}
            await update.message.reply_text("SYSTEM ONLINE\n\n" + self._format_stats(),
                                            reply_markup=_build_main_keyboard())

        # --- /status ---
        async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            user_sessions[user_id] = {"mode": None, "screen": "status"}
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
            user_sessions[user_id] = {"mode": None, "screen": "agent"}
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
            user_sessions[user_id] = {"mode": None, "screen": "module"}
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
            user_sessions[user_id] = {"mode": None, "screen": "upgrade"}
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
            user_sessions[user_id] = {"mode": None, "screen": "progress"}
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
            user_sessions[user_id] = {"mode": None, "screen": "system"}
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
                "📋 XUMOTION COMMANDS\n\n"
                "/start — Main menu & dashboard\n"
                "/status — Operator status\n"
                "/agent — Manage agents\n"
                "/module — Manage modules\n"
                "/upgrade — Enhance operator\n"
                "/progress — Sector & checkpoint\n"
                "/system — Auto, cycle, log, save\n"
                "/help — This guide"
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

            # Always handle Back/Cancel immediately
            if text == "Back":
                session["mode"] = None
                session["screen"] = "main_menu"
                await update.message.reply_text("Kembali ke menu utama.", reply_markup=_build_main_keyboard())
                return
            if text == "Cancel":
                session["mode"] = None
                await update.message.reply_text("Dibatalkan.", reply_markup=_build_main_keyboard())
                return

            # Route button presses according to current screen
            screen = session.get("screen", "main_menu")
            response = None

            if screen == "status":
                if text == "Stats":
                    response = process_command(self.state, "stats")
                elif text == "Core":
                    response = process_command(self.state, "core")
            elif screen == "agent":
                if text == "List Agents":
                    response = process_command(self.state, "modules")
                elif text == "Deploy":
                    session["mode"] = "awaiting_deploy"
                    await update.message.reply_text("Enter agent ID to deploy:", 
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True))
                    return
                elif text == "Undeploy":
                    session["mode"] = "awaiting_undeploy"
                    await update.message.reply_text("Enter agent ID to undeploy:",
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True))
                    return
                elif text == "Merge":
                    session["mode"] = "awaiting_merge"
                    await update.message.reply_text("Enter agent IDs to merge (e.g. 1 2):",
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True))
                    return
                elif text == "Enhance Agent":
                    session["mode"] = "awaiting_enhance"
                    await update.message.reply_text("Enter agent ID to enhance:",
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True))
                    return
            elif screen == "module":
                if text == "List Modules":
                    response = process_command(self.state, "modules")
                elif text == "Install":
                    session["mode"] = "awaiting_module_install"
                    await update.message.reply_text("Enter module ID to install (or leave empty for auto):",
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True))
                    return
                elif text == "Uninstall":
                    session["mode"] = "awaiting_module_uninstall"
                    await update.message.reply_text("Enter module ID to uninstall:",
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True))
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
                # tetap di sub-menu, jangan kirim keyboard utama
                return
        
            # --- Mode input (menunggu input dari pengguna) ---
            if session.get("mode"):
                mode = session["mode"]
                response = None
                if mode == "awaiting_deploy":
                    response = process_command(self.state, f"deploy {text}")
                elif mode == "awaiting_undeploy":
                    response = process_command(self.state, f"undeploy {text}")
                elif mode == "awaiting_merge":
                    response = process_command(self.state, f"merge {text}")
                elif mode == "awaiting_enhance":
                    response = process_command(self.state, f"ea {text}")
                elif mode == "awaiting_module_install":
                    if text.isdigit():
                        response = process_command(self.state, f"install {text}")
                    else:
                        response = process_command(self.state, "install")
                elif mode == "awaiting_module_uninstall":
                    response = process_command(self.state, f"uninstall {text}")

                if response:
                   await update.message.reply_text(response)
                session["mode"] = None
                await update.message.reply_text("Selesai.", reply_markup=_build_main_keyboard())

            # --- Main menu button routing ---
            main_routes = {
                "status": status_cmd,
                "agent": agent_cmd,
                "module": module_cmd,
                "upgrade": upgrade_cmd,
                "progress": progress_cmd,
                "system": system_cmd,
                "help": help_cmd,
            }
            if text.lower() in main_routes:
                return await main_routes[text.lower()](update, context)

            # --- Sub-menu button routing (screen-aware) ---
            screen = session.get("screen", "main_menu") if session else "main_menu"

            if screen == "status":
                sub_map = {"stats": "stats", "core": "core"}
                if text.lower() in sub_map:
                    response = process_command(self.state, sub_map[text.lower()])
                    await update.message.reply_text(response or "No data.")
                    return

            elif screen == "agent":
                if text == "List Agents":
                    response = process_command(self.state, "agents")
                    await update.message.reply_text(response or "No agents.")
                    return
                elif text == "Deploy":
                    session["mode"] = "awaiting_deploy"
                    user_sessions[user_id] = session
                    await update.message.reply_text("Enter agent ID to deploy:")
                    return
                elif text == "Undeploy":
                    session["mode"] = "awaiting_undeploy"
                    user_sessions[user_id] = session
                    await update.message.reply_text("Enter agent ID to undeploy:")
                    return
                elif text == "Merge":
                    session["mode"] = "awaiting_merge"
                    user_sessions[user_id] = session
                    await update.message.reply_text("Enter agent IDs to merge (e.g. 1 2):")
                    return
                elif text == "Enhance Agent":
                    session["mode"] = "awaiting_enhance"
                    user_sessions[user_id] = session
                    await update.message.reply_text("Enter agent ID to enhance:")
                    return

            elif screen == "module":
                if text == "List Modules":
                    response = process_command(self.state, "modules")
                    await update.message.reply_text(response or "No modules.")
                    return
                elif text == "Install":
                    response = process_command(self.state, "install")
                    await update.message.reply_text(response or "Enter module number:")
                    session["mode"] = "awaiting_module_install"
                    user_sessions[user_id] = session
                    return
                elif text == "Uninstall":
                    session["mode"] = "awaiting_module_uninstall"
                    user_sessions[user_id] = session
                    await update.message.reply_text("Enter module ID to uninstall:")
                    return

            elif screen == "upgrade":
                upgrade_map = {
                    "Upgrade ATK": "upgrade atk",
                    "Upgrade DEF": "upgrade def",
                    "Upgrade HP": "upgrade hp",
                    "Upgrade CRIT": "upgrade crit",
                }
                if text in upgrade_map:
                    response = process_command(self.state, upgrade_map[text])
                    await update.message.reply_text(response or "Upgrade processed.")
                    return

            elif screen == "progress":
                progress_map = {
                    "Checkpoint": "checkpoint",
                    "Restore": "restore",
                    "Recompile": "recompile",
                }
                if text in progress_map:
                    response = process_command(self.state, progress_map[text])
                    await update.message.reply_text(response or "Done.")
                    return

            elif screen == "system":
                system_map = {
                    "Auto": "auto",
                    "Cycle": "cycle",
                    "Log": "log",
                    "Save": "save",
                }
                if text in system_map:
                    response = process_command(self.state, system_map[text])
                    await update.message.reply_text(response or "Done.")
                    return

            if not session or not session.get("mode"):
                return  # not in input mode

            mode = session["mode"]
            response = ""

            # --- Agent input ---
            if mode == "awaiting_deploy":
                response = process_command(self.state, f"deploy {text}")
            elif mode == "awaiting_undeploy":
                response = process_command(self.state, f"undeploy {text}")
            elif mode == "awaiting_merge":
                response = process_command(self.state, f"merge {text}")
            elif mode == "awaiting_enhance":
                response = process_command(self.state, f"ea {text}")

            # --- Module input ---
            elif mode == "awaiting_module_install":
                if text.isdigit():
                    response = process_command(self.state, f"install {text}")
                else:
                    response = process_command(self.state, "install")
            elif mode == "awaiting_module_uninstall":
                response = process_command(self.state, f"uninstall {text}")

            if response:
                await update.message.reply_text(response)
            
            # Kembalikan keyboard utama
            session["mode"] = None
            user_sessions[user_id] = session
            await update.message.reply_text("Selesai.", reply_markup=_build_main_keyboard())

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
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=0)

    async def run(self):
        if not TELEGRAM_TOKEN:
            print("TELEGRAM_BOT_TOKEN not set. Bot not started.")
            return
        await self.app.initialize()
        await self.app.start()
        await self._set_bot_commands()
        await self.app.updater.start_polling()
        print("Telegram bot polling started.")
        while self.state.running:
            await asyncio.sleep(1)
        await self.app.stop()


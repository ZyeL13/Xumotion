import os
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from game.engine import process_command
from game.state import GameState
from game.event_logger import event_logger
from systems.progression import required_exp

TELEGRAM_TOKEN = os.environ.get("RPG_BOT_TOKEN", "")

# Authorized Telegram user IDs (comma-separated)
ADMIN_IDS_STR = os.environ.get("TELEGRAM_ADMIN_IDS", "")
ADMIN_IDS = set(ADMIN_IDS_STR.split(",")) if ADMIN_IDS_STR else set()


def _is_authorized(update: Update) -> bool:
    """Allow all if ADMIN_IDS is empty, otherwise check user ID."""
    if not ADMIN_IDS:
        return True
    return str(update.effective_user.id) in ADMIN_IDS


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
            (0, 9): "SANDBOX",
            (10, 19): "RELAY BASIN",
            (20, 29): "COLD STORAGE",
            (30, 39): "MIRROR SECTOR",
            (40, 49): "ARCHIVE LAYER",
            (50, 59): "NULL ZONE",
            (60, 69): "SIGNAL DEPTHS",
            (70, 79): "CORE NETWORK",
            (80, 89): "ECHO VOID",
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
            "",
            "COMMANDS",
            "/stats /enhance /deploy /install",
            "/uninstall /modules /recompile",
            "/core /auto /cycle /log",
            "/checkpoint /restore /help",
        ]

        if log_msg:
            lines.insert(lines.index("COMMANDS") - 1, f"LOG: {log_msg}")

        return "\n".join(lines)

    async def _set_bot_commands(self):
        commands = [
            BotCommand("start", "System status"),
            BotCommand("stats", "Operator stats"),
            BotCommand("enhance", "Enhance module (atk|defense|max_hp|crit_rate)"),
            BotCommand("deploy", "Deploy agent"),
            BotCommand("undeploy", "Undeploy agent"),
            BotCommand("merge", "Merge 3 agents: /merge <unit_name> <slot1> <slot2> <slot3>"),
            BotCommand("install", "Install module from bay"),
            BotCommand("uninstall", "Uninstall module by slot"),
            BotCommand("modules", "View module bay & agents"),
            BotCommand("recompile", "Recompile core"),
            BotCommand("core", "Check core status"),
            BotCommand("auto", "Toggle auto-enhance"),
            BotCommand("cycle", "Claim cycle deposit"),
            BotCommand("log", "View log entries"),
            BotCommand("checkpoint", "Force save"),
            BotCommand("restore", "Restore operator"),
            BotCommand("help", "Show help"),
            BotCommand("ea", "Enhance agent DPS"),
        ]
        await self.app.bot.set_my_commands(commands)

    def _register_handlers(self):
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("SYSTEM ONLINE\n\n" + self._format_stats())

        async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(self._format_stats())

        async def enhance(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            target = " ".join(context.args) if context.args else ""
            if not target:
                await update.message.reply_text("Usage: /enhance atk | defense | max_hp | crit_rate")
                return
            response = process_command(self.state, f"enhance {target}")
            await update.message.reply_text(response)

        async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            agent_type = context.args[0] if context.args else ""
            if agent_type == "list":
                response = process_command(self.state, "deploy list")
            else:
                response = process_command(self.state, f"deploy {agent_type}")
            await update.message.reply_text(response)

        async def undeploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            if not context.args:
                await update.message.reply_text("USAGE: /undeploy <agent name/number>")
                return
            response = process_command(self.state, f"undeploy {context.args[0]}")
            await update.message.reply_text(response)

        async def merge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            if len(context.args) < 4:
                await update.message.reply_text(
                    "USAGE: /merge <unit_name> <slot1> <slot2> <slot3>\n"
                    "Example: /merge Echo 1 2 3"
                )
                return
            unit_name = context.args[0]
            try:
                slots = [int(x) for x in context.args[1:4]]
            except ValueError:
                await update.message.reply_text("Slots must be integers. Example: /merge Echo 1 2 3")
                return
            command_str = f"merge {unit_name} {slots[0]} {slots[1]} {slots[2]}"
            response = process_command(self.state, command_str)
            await update.message.reply_text(response)

        async def install(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            if not context.args:
                response = process_command(self.state, "install")
                await update.message.reply_text(response)
                return
            try:
                index = int(context.args[0])
            except ValueError:
                await update.message.reply_text("Usage: /install (auto) or /install <bay number>")
                return
            response = process_command(self.state, f"install {index}")
            await update.message.reply_text(response)

        async def uninstall(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            if not context.args:
                await update.message.reply_text("Usage: /uninstall injector | barrier | cache")
                return
            response = process_command(self.state, f"uninstall {context.args[0]}")
            await update.message.reply_text(response)

        async def modules(update: Update, context: ContextTypes.DEFAULT_TYPE):
            p = self.state.player
            if p.agents:
                agent_lines = []
                for i, a in enumerate(p.agents):
                    deployed = " [ACTIVE]" if a.deployed else ""
                    agent_lines.append(
                        f"[{i+1}] {a.name}{deployed} (Tier: {a.tier}, Lv.{a.level}, DPS {a.dps})"
                    )
                agents_str = "\n".join(agent_lines)
            else:
                agents_str = "none"

            slots_info = f"SLOTS: {p.get_deployed_count()}/{p.max_agent_slots} active"

            if p.inventory:
                mod_lines = []
                for i, mod in enumerate(p.inventory):
                    stat_parts = []
                    if mod.atk_bonus:
                        stat_parts.append(f"ATK+{mod.atk_bonus}")
                    if mod.def_bonus:
                        stat_parts.append(f"DEF+{mod.def_bonus}")
                    if mod.hp_bonus:
                        stat_parts.append(f"HP+{mod.hp_bonus}")
                    if mod.crit_rate_bonus:
                        stat_parts.append(f"CRIT+{mod.crit_rate_bonus:.1%}")
                    stats = " | ".join(stat_parts) or "no stats"
                    installed = " [INSTALLED]" if mod.installed else ""
                    mod_lines.append(f"[{i+1}] {mod.name}{installed}\n    {stats}")
                bay_str = "\n".join(mod_lines)
            else:
                bay_str = "empty"

            msg = (
                f"AGENTS:\n{agents_str}\n\n"
                f"{slots_info}\n\n"
                f"MODULE BAY ({len(p.inventory)}):\n{bay_str}"
            )
            await update.message.reply_text(msg)

        async def recompile(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            response = process_command(self.state, "recompile")
            await update.message.reply_text(response)

        async def core(update: Update, context: ContextTypes.DEFAULT_TYPE):
            response = process_command(self.state, "core")
            await update.message.reply_text(response)

        async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            mode = context.args[0] if context.args else ""
            response = process_command(self.state, f"auto {mode}")
            await update.message.reply_text(response)

        async def cycle(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            response = process_command(self.state, "cycle")
            await update.message.reply_text(response)

        async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
            response = process_command(self.state, "log")
            await update.message.reply_text(response)

        async def checkpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            response = process_command(self.state, "checkpoint")
            await update.message.reply_text(response)

        async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            response = process_command(self.state, "restore")
            await update.message.reply_text(response)

        async def enhance_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not _is_authorized(update):
                await update.message.reply_text("❌ Unauthorized.")
                return
            if not context.args:
                await update.message.reply_text("Usage: /ea <agent name>")
                return
            response = process_command(self.state, f"ea {context.args[0]}")
            await update.message.reply_text(response)

        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            response = process_command(self.state, "help")
            await update.message.reply_text(response)

        # Register all handlers
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(CommandHandler("stats", stats))
        self.app.add_handler(CommandHandler("enhance", enhance))
        self.app.add_handler(CommandHandler("deploy", deploy))
        self.app.add_handler(CommandHandler("undeploy", undeploy))
        self.app.add_handler(CommandHandler("merge", merge_cmd))
        self.app.add_handler(CommandHandler("install", install))
        self.app.add_handler(CommandHandler("uninstall", uninstall))
        self.app.add_handler(CommandHandler("modules", modules))
        self.app.add_handler(CommandHandler("recompile", recompile))
        self.app.add_handler(CommandHandler("core", core))
        self.app.add_handler(CommandHandler("auto", auto))
        self.app.add_handler(CommandHandler("cycle", cycle))
        self.app.add_handler(CommandHandler("log", log))
        self.app.add_handler(CommandHandler("checkpoint", checkpoint))
        self.app.add_handler(CommandHandler("restore", restore))
        self.app.add_handler(CommandHandler("ea", enhance_agent))
        self.app.add_handler(CommandHandler("enhance_agent", enhance_agent))
        self.app.add_handler(CommandHandler("help", help_cmd))

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

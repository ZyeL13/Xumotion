import json
import asyncio
import http.server
import os
import time
import urllib.parse
from pathlib import Path

from game.state_manager import state_manager
from game.event_logger import event_logger
from game.state import GameState

# Config
WEB_HOST = os.environ.get("WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.environ.get("WEB_PORT", "8080"))
WS_HOST = os.environ.get("WS_HOST", "127.0.0.1")
WS_PORT = int(os.environ.get("WS_PORT", "8081"))
WEB_AUTH_TOKEN = os.environ.get("WEB_AUTH_TOKEN", "")

STATIC_DIR = Path(__file__).parent / "static"

# Global websocket clients
websockets_clients = []
MAX_WS_CLIENTS = 100


# ---------- Auth helper ----------
def extract_user_id_from_request(handler) -> int | None:
    """
    Extract user ID from:
    1. X-Telegram-InitData header
    2. X-User-ID header (dev mode)
    3. query param initData
    4. query param user_id (legacy)
    """
    # Header: Telegram Mini App
    header_init = handler.headers.get("X-Telegram-InitData")
    if header_init:
        try:
            parsed = dict(urllib.parse.parse_qsl(header_init))
            user_field = parsed.get("user")
            if user_field:
                user_data = json.loads(user_field)
                if "id" in user_data:
                    return int(user_data["id"])
        except Exception:
            pass

    # Header: dev mode
    dev_user = handler.headers.get("X-User-ID")
    if dev_user and dev_user.isdigit():
        return int(dev_user)

    # Query param: initData
    parsed_qs = urllib.parse.urlparse(handler.path).query
    qs_params = urllib.parse.parse_qs(parsed_qs)
    init_data = qs_params.get("initData", [None])[0]
    if init_data:
        try:
            parsed = dict(urllib.parse.parse_qsl(init_data))
            user_field = parsed.get("user")
            if user_field:
                user_data = json.loads(user_field)
                if "id" in user_data:
                    return int(user_data["id"])
        except Exception:
            pass

    # Query param: user_id (legacy)
    raw = qs_params.get("user_id", [None])[0]
    if raw and raw.isdigit():
        return int(raw)

    return None


# ---------- Zone helper ----------
def _get_zone(sector: int) -> str:
    zones = [
        (0, 9, "SANDBOX"),
        (10, 19, "RELAY BASIN"),
        (20, 29, "COLD STORAGE"),
        (30, 39, "MIRROR SECTOR"),
        (40, 49, "ARCHIVE LAYER"),
        (50, 59, "NULL ZONE"),
        (60, 69, "SIGNAL DEPTHS"),
        (70, 79, "CORE NETWORK"),
        (80, 89, "ECHO VOID"),
        (90, 99, "GENESIS RING"),
    ]
    for lo, hi, name in zones:
        if lo <= sector <= hi:
            return name
    return "DEEP LAYER" if sector > 99 else "UNKNOWN"


# ---------- HTTP Handler ----------
class APIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/v1/state"):
            self.handle_get_state()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/v1/action"):
            self.handle_post_action()
        else:
            self.send_error(404)

    # ---------- GET /api/v1/state ----------
    def handle_get_state(self):
        user_id = extract_user_id_from_request(self)
        if user_id is None:
            self.send_error(401, "Authentication required")
            return

        state = state_manager.load_or_create(telegram_id=user_id)
        response = self._build_state_response(state)
        self._send_json(response)

    def _build_state_response(self, state: GameState) -> dict:
        p = state.player
        e = state.enemy

        try:
            from systems.progression import required_exp
            exp_needed = required_exp(p.level)
        except Exception:
            exp_needed = 0

        return {
            "player": {
                "level": p.level,
                "exp": p.exp,
                "exp_needed": exp_needed,
                "hp": p.hp,
                "max_hp": p.effective_max_hp,
                "atk": p.atk,
                "dps": p.dps,
                "defense": p.defense,
                "crit_rate": p.crit_rate,
                "crit_damage": p.crit_damage,
                "gold": p.gold,
                "input_credits": p.input_credits,
                "core_points": p.core_points,
                "auto_enhance": p.auto_enhance,
                "paused": state.paused,
                "max_agent_slots": p.max_agent_slots,
                "deployed_count": p.get_deployed_count(),
                "last_daily_claim": getattr(p, 'last_daily_claim', 0),  # ADD THIS
            },
            "enemy": {
                "name": e.name,
                "hp": e.hp,
                "max_hp": e.max_hp,
                "rarity": e.rarity,
                "is_boss": state.boss_active,
                "boss_timer": state.boss_timer if state.boss_active else None,
                "reward_gold": e.reward_gold,   # ⬅ TAMBAH
                "reward_exp": e.reward_exp,     # ⬅ TAMBAH
            },
            "sector": {
                "sector": state.sector,
                "substage": state.substage,
                "zone": _get_zone(state.sector),
                "boss_active": state.boss_active,
                "kills_in_stage": state.kills_in_stage,  # ADD THIS
            },
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "tier": a.tier,
                    "level": a.level,
                    "dps": a.dps,
                    "deployed": a.deployed,
                }
                for a in p.agents
            ],
            "modules": [
                {
                    "name": m.name,
                    "slot": m.slot.value if hasattr(m.slot, "value") else m.slot,
                    "rarity": m.rarity.value if hasattr(m.rarity, "value") else m.rarity,
                    "installed": m.installed,
                    "atk_bonus": getattr(m, "atk_bonus", 0),
                    "def_bonus": getattr(m, "def_bonus", 0),
                    "hp_bonus": getattr(m, "hp_bonus", 0),
                    "crit_rate_bonus": getattr(m, "crit_rate_bonus", 0),
                }
                for m in p.inventory
            ],
        }

    # ---------- POST /api/v1/action ----------
    def handle_post_action(self):
        user_id = extract_user_id_from_request(self)
        if user_id is None:
            user_id = 0  # dev fallback

        # Read body
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        action = payload.get("action", "")
        params = payload.get("params", {})

        # Load state
        state = state_manager.load_or_create(telegram_id=user_id)

        with state.lock:
            try:
                result = self._dispatch_action(state, action, params)
                state_manager.save(state)
                self._send_json({
                    "success": True,
                    "message": result,
                    "state": self._build_state_response(state),
                })
            except Exception as e:
                self._send_json({"success": False, "message": str(e)})

    def _dispatch_action(self, state: GameState, action: str, params: dict) -> str:
        # === Direct handlers (no legacy command parsing) ===
        if action == "toggle_auto":
            state.player.auto_enhance = not state.player.auto_enhance
            return "Auto-enhance enabled." if state.player.auto_enhance else "Auto-enhance disabled."

        if action == "toggle_pause":
            state.paused = not state.paused
            return "Runtime paused." if state.paused else "Runtime resumed."

        if action == "claim_daily":
            from systems.daily import claim_daily, can_claim
            if can_claim():
                result = claim_daily(state)
                return result if result else "Daily reward claimed."
            return "Daily already claimed today."

        if action == "start_boss":
            if state.substage != 10:
                return "No active boss."
    
            if not state.boss_active:
                state.boss_active = True
                if state.boss_timer <= 0:
                    if state.sector <= 5:
                        state.boss_timer = 60.0
                    elif state.sector <= 15:
                        state.boss_timer = 45.0
                    else:
                        state.boss_timer = 30.0
                state.enemy = Enemy.generate(state.sector, 10, state.player)
                return f"Boss encounter started — {state.enemy.name}"
            else:
                return "Boss fight already in progress."

        # === Legacy command mapping ===
        from game.engine import process_command

        mapping = {
            "enhance":          "enhance {stat}",
            "deploy_agent":     "deploy {agent_id}",
            "undeploy_agent":   "undeploy {agent_id}",
            "merge_agents":     "merge {ids}",
            "enhance_agent":    "ea {agent_id}",
            "install_module":   "install {index}",
            "uninstall_module": "uninstall {slot}",
            "recompile":        "recompile",
        }

        if action in mapping:
            cmd = mapping[action].format(**params)
            return process_command(state, cmd)

        raise ValueError(f"Unknown action: {action}")

    # ---------- Helpers ----------
    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Telegram-InitData, X-User-ID")
        self.end_headers()

    def log_message(self, format, *args):
        pass


# ---------- WebSocket ----------
async def ws_handler(websocket):
    if len(websockets_clients) >= MAX_WS_CLIENTS:
        await websocket.close(code=1008, reason="Server full")
        return
    websockets_clients.append(websocket)
    try:
        async for _ in websocket:
            pass
    except Exception:
        if websocket in websockets_clients:
            websockets_clients.remove(websocket)


async def ws_broadcast():
    while True:
        ev = event_logger.poll()
        if ev and websockets_clients:
            data = json.dumps({
                "timestamp": ev.timestamp,
                "type": ev.event_type,
                "message": ev.message,
            })
            to_remove = []
            for ws in websockets_clients:
                try:
                    await ws.send(data)
                except Exception:
                    to_remove.append(ws)
            for ws in to_remove:
                if ws in websockets_clients:
                    websockets_clients.remove(ws)
        await asyncio.sleep(0.5)


async def run_ws_server():
    import websockets
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        await ws_broadcast()


def run_http_server():
    import socket
    server = http.server.HTTPServer((WEB_HOST, WEB_PORT), APIHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.timeout = 1
    print(f"Web dashboard: http://{WEB_HOST}:{WEB_PORT}")
    while True:
        server.handle_request()


def start_web():
    import threading
    threading.Thread(target=run_http_server, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_ws_server()), daemon=True).start()

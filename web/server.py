import json
import asyncio
import http.server
import threading
import os
from urllib.parse import urlparse
from pathlib import Path
from game.event_logger import event_logger

# Configurable host/port — defaults to localhost for security
WEB_HOST = os.environ.get("WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.environ.get("WEB_PORT", "8080"))
WS_HOST = os.environ.get("WS_HOST", "127.0.0.1")
WS_PORT = int(os.environ.get("WS_PORT", "8081"))

game_state = None
websockets_clients = []
MAX_WS_CLIENTS = 100

# Path ke folder static
STATIC_DIR = Path(__file__).parent / "static"


class ConsoleHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        from urllib.parse import parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
    
        # Untuk sementara, ambil user_id dari query parameter
        user_id = params.get('user_id', [None])[0]
        if user_id:
            user_id = int(user_id)
    
        if parsed.path == "/api/state":
            self._api_state(user_id)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/command":
            self._api_command()
        else:
            self.send_error(404)

    def _api_state(self, user_id=None):
        if user_id:
            state = load_game(user_id)
            if state is None:
                self.send_error(404, "Game state not found")
                return
        else:
           state = game_state  # fallback ke global state
        with game_state.lock:
            p = game_state.player
            e = game_state.enemy
            data = {
                "stage": f"{game_state.sector}.{game_state.substage}",
                "kills": game_state.kills_in_stage,
                "player": {
                    "level": p.level,
                    "exp": p.exp,
                    "exp_needed": required_exp(p.level, LEVEL_EXP_BASE, LEVEL_EXP_GROWTH),
                    "hp": p.hp,
                    "max_hp": p.effective_max_hp,
                    "atk": p.atk,
                    "dps": p.dps,
                    "defense": p.defense,
                    "crit_rate": p.crit_rate,
                    "crit_damage": p.crit_damage,
                    "gold": p.gold,
                    "shards": p.core_points,
                    "auto_enhance": getattr(p, "auto_enhance", False),
                    "agents": [
                        {
                            "id": a.id if hasattr(a, 'id') else i + 1,
                            "name": a.name,
                            "tier": a.tier,
                            "level": a.level,
                            "dps": a.dps,
                            "deployed": a.deployed
                        } for i, a in enumerate(p.agents)
                    ],
                    "inventory": [
                        {
                            "name": m.name,
                            "rarity": m.rarity.value if hasattr(m.rarity, 'value') else m.rarity,
                            "slot": m.slot.value if hasattr(m.slot, 'value') else m.slot,
                            "installed": m.installed,
                            "atk_bonus": getattr(m, 'atk_bonus', 0),
                            "def_bonus": getattr(m, 'def_bonus', 0),
                            "hp_bonus": getattr(m, 'hp_bonus', 0),
                            "crit_rate_bonus": getattr(m, 'crit_rate_bonus', 0),
                        } for m in p.inventory
                    ],
                    "inventory_count": len(p.inventory),
                    "max_agent_slots": p.max_agent_slots,
                    "deployed_count": p.get_deployed_count(),
                },
                "enemy": {
                    "name": e.name,
                    "hp": e.hp,
                    "max_hp": e.max_hp,
                    "rarity": e.rarity,
                    "reward_gold": e.reward_gold,
                    "reward_exp": e.reward_exp,
                }
            }
            self._json_response(data)

    def _api_command(self):
        import hmac
        token = os.environ.get("WEB_AUTH_TOKEN", "")
        if token:
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or not hmac.compare_digest(auth[7:], token):
                self.send_error(403, "Forbidden")
                return
        else:
            remote = self.client_address[0]
            if remote not in ("127.0.0.1", "localhost", "::1"):
                self.send_error(403, "API not exposed to network")
                return

        # Read body OUTSIDE the lock to prevent blocking the game loop
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            cmd = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        from game.engine import process_command
        # process_command already handles state.lock internally
        result = process_command(game_state, cmd.get("text", ""))
        self._json_response({"response": result})

    def _json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP request logging to stdout."""
        pass


async def ws_handler(websocket):
    global websockets_clients
    if len(websockets_clients) >= MAX_WS_CLIENTS:
        await websocket.close(code=1008, reason="Server full")
        return
    websockets_clients.append(websocket)
    try:
        async for _ in websocket:
            pass
    except Exception:
        websockets_clients.remove(websocket)
    finally:
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
            disconnected = []
            for ws in websockets_clients:
                try:
                    await ws.send(data)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                if ws in websockets_clients:
                    websockets_clients.remove(ws)
        await asyncio.sleep(0.5)


async def run_ws_server():
    import websockets
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        await ws_broadcast()


def run_http_server():
    import socket
    server = http.server.HTTPServer((WEB_HOST, WEB_PORT), ConsoleHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.timeout = 1
    print(f"Web dashboard: http://{WEB_HOST}:{WEB_PORT}")
    while game_state is not None and game_state.running:
        server.handle_request()


def start_web(state):
    global game_state
    game_state = state
    threading.Thread(target=run_http_server, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_ws_server()), daemon=True).start()

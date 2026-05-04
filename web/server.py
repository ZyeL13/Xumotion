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

# Path ke folder static
STATIC_DIR = Path(__file__).parent / "static"


class ConsoleHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self._api_state()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/command":
            self._api_command()
        else:
            self.send_error(404)

    def _api_state(self):
        with game_state.lock:
            p = game_state.player
            e = game_state.enemy
            data = {
                "stage": game_state.current_stage,
                "kills": game_state.kills_in_stage,
                "player": {
                    "level": p.level,
                    "exp": p.exp,
                    "hp": p.hp,
                    "max_hp": p.effective_max_hp,
                    "atk": p.atk,
                    "dps": p.dps,
                    "defense": p.defense,
                    "crit_rate": p.crit_rate,
                    "crit_damage": p.crit_damage,
                    "gold": p.gold,
                    "agents": [{"name": a.name, "dps": a.dps} for a in p.agents],
                    "inventory_count": len(p.inventory),
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
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        cmd = json.loads(body)
        from game.engine import process_command
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
    websockets_clients.append(websocket)
    try:
        async for _ in websocket:
            pass
    except Exception:
        pass
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
    server = http.server.HTTPServer((WEB_HOST, WEB_PORT), ConsoleHandler)
    print(f"Web dashboard: http://{WEB_HOST}:{WEB_PORT}")
    server.serve_forever()


def start_web(state):
    global game_state
    game_state = state
    threading.Thread(target=run_http_server, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_ws_server()), daemon=True).start()

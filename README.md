```markdown
# XUMOTION — Operator Console for Idle Systems

**Operator Console for Idle Systems** with Telegram command interface, web dashboard, and terminal monitor.

---

## 🔐 Security Model

XUMOTION is designed to be run locally or on a private server. By default, all external interfaces are bound to `127.0.0.1` (localhost) to prevent unauthorized access.

### Environment Variables
- **`RPG_BOT_TOKEN`**: Required for Telegram bot. Keep this secret.
- **`WEB_HOST` / `WS_HOST`**: Set to `127.0.0.1` for local-only access. To expose the dashboard, use `0.0.0.0` and configure a firewall.
- **`WEB_AUTH_TOKEN`** (optional): If the web API is exposed to the internet, set a strong token and require it in the `Authorization` header.

### Data Protection
- All game state is stored locally in `saves/`. These files should be readable/writable only by the owner (`chmod 600 saves/*`).
- The `.env` file is excluded from version control (`.gitignore`).

### Command Safety
- All user input is processed as command strings; no shell execution or eval.
- Commands are validated by a whitelist parser; unknown commands are rejected.

### Randomness
- Randomness is provided by Python's `random` module and is **not cryptographically secure**. It is suitable for gameplay but **not for generating keys, tokens, or blockchain commitments**.

### External Services
- The Telegram bot uses the official `python-telegram-bot` library and communicates only with Telegram's API.
- The web dashboard serves static files and a read‑only event stream via WebSocket. No sensitive data is transmitted.

### Audit
- Dependencies can be audited with `pip install safety && safety check`.
- Static analysis: `ruff check .` (linter) and `mypy` (type checker).

---

## 🛠 Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env with your Telegram token
python main.py
```

Access the dashboard at http://localhost:8080.

---

🧩 Architecture

```
game/        – core engine, combat, formulas, event logger
systems/     – economy, modules, prestige, autobuy, daily, loot
models/      – player, enemy, agent, module
interfaces/  – telegram bot, cli monitor
web/         – web dashboard (FastAPI replacement: http.server + WebSocket)
data/        – JSON configuration files (enemies, agents, upgrades, progression)
saves/       – local save files (ignored by Git)
```

---

📡 Interfaces

· Telegram Bot – 20+ commands, plain-text UI.
· Web Dashboard – real‑time stats, agent management, event feed.
· CLI Monitor – terminal display (python run_monitor.py).

---

Versioning

· v0.1 – MVP: idle loop, combat, shop, prestige, Telegram bot.
· v0.2 – Hardening: security config, slot‑based agents, merge, web dashboard.

---

📦 Requirements

· Python 3.11+
· python-telegram-bot
· websockets
· rich
· python-dotenv


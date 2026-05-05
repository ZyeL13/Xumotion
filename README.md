```markdown
# XUMOTION — Systems Console

⚡ **Autonomous Agent Operations Simulator**

XUMOTION adalah game idle RPG bertema **operator console** untuk infrastruktur otonom. Jalankan loop game, kelola agen, pasang modul, dan recompile core untuk multiplier permanen — semuanya melalui Telegram, Web Dashboard, atau CLI Monitor.

---

## ✨ Fitur Utama

- **Auto-Combat Loop** — Player & Entity saling serang dua arah dengan scaling eksponensial.
- **Agent System** — Rekrut, deploy, enhance, merge, dan atur slot agen aktif (4 tier, 7 varian).
- **Module System** — Loot, pasang, scrap, dan upgrade modul (3 slot, 5 raritas).
- **Recompile (Prestige)** — Reset progres untuk Core Points dan multiplier permanen.
- **Cycle (Daily Rewards)** — Klaim deposit kredit harian (7 hari berturut-turut).
- **Log Entries (Achievements)** — 11 achievement yang auto-unlock beserta hadiahnya.
- **Auto-Enhance** — Mode idle penuh: upgrade modul & deploy agen termurah otomatis.
- **Offline Rewards** — Kredit tetap terkumpul saat game mati (capped 8 jam).
- **Prime Instance** — Boss spesial muncul setiap 5 menit dengan hadiah 3x lipat.
- **Zone Flavor** — 10 zona tematik berubah setiap 10 sektor (Sandbox → Genesis Ring).

### Interfaces
- **🤖 Telegram Bot** — 20+ command, plain-text UI, admin authorization.
- **🌐 Web Dashboard** — Real-time state, manajemen agen/modul, AI Console, live events.
- **⌨️ CLI Monitor** — Tampilan terminal dengan Rich (opsional).

---

## 🏗️ Arsitektur

```

idle-rpg/
├── main.py                  # Entry: game loop + Telegram + Web server
├── run_monitor.py            # Entry: CLI monitor mode
├── .env                      # Token & konfigurasi (tidak di-commit)
├── .env.example              # Template konfigurasi
├── data/                     # JSON config (enemies, agents, upgrades, dll)
│   ├── enemies.json
│   ├── agents.json
│   ├── upgrades.json
│   ├── progression.json
│   ├── achievements.json
│   └── daily.json
├── game/                     # Core engine & systems
│   ├── engine.py             # Command processor + game loop
│   ├── combat.py             # Auto-battle logic
│   ├── formulas.py           # Stateless math functions
│   ├── state.py              # GameState dataclass + lock
│   ├── save_manager.py       # JSON save/load dengan versioning
│   ├── event_logger.py       # Event bus (queue-based)
│   ├── registry.py           # Upgrade & Agent registries
│   └── ...
├── models/                   # Data classes
│   ├── player.py             # Player state + effective stats
│   ├── enemy.py              # Entity generation (normal, boss, prime)
│   ├── agent.py              # Agent (tier, level, deployed)
│   └── module.py             # Module (slot, rarity, stats)
├── systems/                  # Gameplay systems
│   ├── economy.py            # Enhance, deploy, merge, enhance agent
│   ├── modules.py            # Install/uninstall/auto-install logic
│   ├── loot.py               # Module drop generation
│   ├── prestige.py           # Recompile system
│   ├── autobuy.py            # Auto-enhance logic
│   ├── daily.py              # Cycle rewards (tamper-resistant)
│   └── ...
├── interfaces/               # Communication layers
│   ├── telegram_bot.py       # Telegram bot (17 commands)
│   └── cli_monitor.py        # Terminal dashboard
├── web/                      # Web dashboard
│   ├── server.py             # HTTP + WebSocket server
│   └── static/
│       ├── css/console.css   # Dark theme, system operator aesthetic
│       ├── js/dashboard.js   # Dashboard logic, TWA, AI streaming
│       └── index.html        # Dashboard structure
└── saves/                    # Local save files (ignored by Git)

```

---

## 🚀 Quick Start

### Prasyarat
- Python 3.11+
- pip

### Instalasi
```bash
git clone https://github.com/ZyeL13/Xumotion.git
cd Xumotion
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan token Telegram Bot dari @BotFather
```

Menjalankan

```bash
# Mode penuh (Telegram bot + Web dashboard + Game loop)
python main.py

# Mode CLI monitor (tanpa Telegram bot)
python run_monitor.py
```

Buka http://localhost:8080 untuk mengakses web dashboard.

---

📡 Interfaces & Commands

Telegram Bot

Command Description
/start System status
/stats Operator stats
/enhance <stat> Enhance module (atk/defense/max_hp/crit_rate)
/deploy [agent] Deploy agent (default: termurah)
/undeploy <agent> Remove agent from active slot
/merge <n> <n> <n> Merge 3 agents of same tier
/install [n] Install module (auto: best-in-slot + scrap)
/uninstall <slot> Uninstall module
/modules View agents & module bay
/recompile Recompile core (prestige)
/core Check core points
/auto Toggle auto-enhance
/cycle Claim daily deposit
/log View log entries (achievements)
/checkpoint Force save
/restore Restore after death
/ea <agent> Enhance agent DPS

Web Dashboard

· Dashboard Tab: Sektor aktif, integrity bar, stat cards, live event stream.
· Agents Tab: Grid agent, deploy/recall/upgrade.
· Modules Tab: Grid modul, filter rarity/slot, install/remove/enhance.
· Progression Tab: Rank, EXP bar, milestones, unlock tracker.
· AI Console (NEXUS-AI): Streaming chat, analisis sektor/rekomendasi/audit.

---

⚙️ Konfigurasi

Semua variabel environment ada di .env:

Variable Default Deskripsi
RPG_BOT_TOKEN — Token Telegram Bot
TELEGRAM_ADMIN_IDS — ID pengguna yang diizinkan akses (kosong = semua)
WEB_HOST 127.0.0.1 Host web dashboard
WEB_PORT 8080 Port web dashboard
WEB_AUTH_TOKEN — Token opsional untuk akses web API
WS_HOST 127.0.0.1 Host WebSocket
WS_PORT 8081 Port WebSocket

---

🔐 Security Model

· Local-first: Semua interface default ke 127.0.0.1 (localhost).
· Save validation: Data save divalidasi dengan batas wajar per stage.
· Input sanitization: Command diparsing dengan whitelist, karakter valid terbatas.
· Telegram auth: Admin ID opsional untuk membatasi akses.
· Daily checksum: File daily dilindungi hash agar tidak bisa dimanipulasi manual.
· WebSocket limit: Maksimum 100 koneksi simultan.

---

📈 Game Balance

Semua variabel balancing ada di data/*.json. Formula kunci:

· Enemy HP: 50 × 1.18^stage
· Enemy ATK: 3 × 1.08^stage
· Credit Reward: 10 × 1.20^stage
· EXP Reward: 5 × 1.14^stage
· Level EXP Required: 20 × 1.20^rank
· Upgrade Cost: base_cost × growth^level

---

🧱 Tech Stack

· Core: Python 3.11, dataclasses, threading
· Telegram: python-telegram-bot
· Web: http.server, websockets, vanilla JS
· CLI: rich
· Data: JSON (config & save)
· Hardening: hmac, hashlib

---

📝 Versioning

· v0.1 — MVP: idle loop, combat, shop, prestige, Telegram bot.
· v0.2 — Hardening: security, slot agents, merge, save validation.
· v0.3 — Web dashboard, AI console, interaction feedback, live events.

---

📦 License

Proyek ini dilisensikan di bawah MIT License.
Dibuat oleh @ZyeL13.
"Bukan hacker. Bukan warrior. Systems architect yang ngurus mesin hidup." 🔧


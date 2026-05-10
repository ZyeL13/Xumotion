"""
game/database.py — SQLite database backend untuk XUMOTION.
"""
import sqlite3
import json
import os
import time
from pathlib import Path

DB_PATH = "saves/xumotion.db"


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables and migrate columns if needed."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
            last_login REAL NOT NULL DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Game state table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            user_id INTEGER PRIMARY KEY,
            sector INTEGER NOT NULL DEFAULT 1,
            substage INTEGER NOT NULL DEFAULT 1,
            boss_active INTEGER NOT NULL DEFAULT 0,
            boss_timer REAL NOT NULL DEFAULT 0.0,
            kills_in_stage INTEGER NOT NULL DEFAULT 0,
            player_data TEXT NOT NULL,
            enemy_data TEXT,
            last_save REAL NOT NULL DEFAULT 0,
            paused INTEGER NOT NULL DEFAULT 0,
            input_credits INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Migrations
    def column_exists(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())

    migrations = [
        ("paused", "INTEGER NOT NULL DEFAULT 0"),
        ("input_credits", "INTEGER NOT NULL DEFAULT 0"),
        ("last_save", "REAL NOT NULL DEFAULT 0"),
        ("enemy_data", "TEXT"),
    ]

    for col_name, col_def in migrations:
        if not column_exists("game_state", col_name):
            cursor.execute(f"ALTER TABLE game_state ADD COLUMN {col_name} {col_def}")

    conn.commit()
    conn.close()


def get_or_create_user(telegram_id: int, username: str = None) -> int:
    """Get or create user, return internal user_id."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()

    if row:
        user_id = row['id']
        cursor.execute(
            "UPDATE users SET last_login = strftime('%s', 'now'), username = ? WHERE id = ?",
            (username, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        user_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return user_id


def load_game_state(user_id: int) -> dict | None:
    """Load game state for a user."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sector, substage, boss_active, boss_timer, kills_in_stage,
               player_data, enemy_data, last_save, paused, input_credits
        FROM game_state
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "sector": row['sector'],
            "substage": row['substage'],
            "boss_active": bool(row['boss_active']),
            "boss_timer": row['boss_timer'],
            "kills_in_stage": row['kills_in_stage'],
            "player_data": json.loads(row['player_data']),
            "enemy": json.loads(row['enemy_data']) if row['enemy_data'] else None,
            "last_save": row['last_save'],
            "paused": bool(row['paused']),
            "input_credits": row['input_credits'],
        }
    return None


def save_game_state(user_id: int, state: dict) -> None:
    """Save game state for a user."""
    conn = _get_connection()
    cursor = conn.cursor()

    player_json = json.dumps(state['player'])
    enemy_json = json.dumps(state.get('enemy')) if state.get('enemy') else None

    cursor.execute("""
        INSERT INTO game_state (
            user_id, sector, substage, boss_active, boss_timer,
            kills_in_stage, player_data, enemy_data, last_save, paused, input_credits
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            sector = excluded.sector,
            substage = excluded.substage,
            boss_active = excluded.boss_active,
            boss_timer = excluded.boss_timer,
            kills_in_stage = excluded.kills_in_stage,
            player_data = excluded.player_data,
            enemy_data = excluded.enemy_data,
            last_save = excluded.last_save,
            paused = excluded.paused,
            input_credits = excluded.input_credits
    """, (
        user_id,
        state.get('sector', 1),
        state.get('substage', 1),
        int(state.get('boss_active', False)),
        state.get('boss_timer', 0.0),
        state.get('kills_in_stage', 0),
        player_json,
        enemy_json,
        state.get('last_save', time.time()),
        int(state.get('paused', False)),
        state.get('input_credits', 0),
    ))

    conn.commit()
    conn.close()


def migrate_json_to_db():
    """Migrate legacy JSON save to SQLite."""
    json_path = Path("saves/savegame.json")
    if not json_path.exists():
        print("No legacy savegame.json found.")
        return

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print("Legacy save corrupted.")
        return

    user_id = get_or_create_user(0, "legacy_user")

    old_stage = data.get('current_stage', 1)
    sector = ((old_stage - 1) // 10) + 1
    substage = ((old_stage - 1) % 10) + 1

    state = {
        'sector': sector,
        'substage': substage,
        'boss_active': data.get('boss_active', False),
        'boss_timer': data.get('boss_timer', 0.0),
        'kills_in_stage': data.get('kills_in_stage', 0),
        'player': data.get('player', {}),
        'enemy': data.get('enemy'),
        'last_save': time.time(),
        'paused': False,
        'input_credits': 0,
    }

    save_game_state(user_id, state)
    print(f"Migrated legacy save to user {user_id}")

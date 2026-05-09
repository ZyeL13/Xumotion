"""
game/database.py — SQLite database backend untuk XUMOTION.

Modul ini menyediakan:
- Inisialisasi database (tabel users, game_state)
- Fungsi load/save state game berdasarkan user_id
- Migrasi dari format JSON lama
"""

import sqlite3
import json
import os
import time
from pathlib import Path

DB_PATH = "saves/xumotion.db"

def _get_connection() -> sqlite3.Connection:
    """Mendapatkan koneksi ke database SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging untuk performa
    return conn

def init_db():
    """Membuat tabel jika belum ada."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
            last_login REAL NOT NULL DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            user_id INTEGER PRIMARY KEY,
            sector INTEGER NOT NULL DEFAULT 1,
            substage INTEGER NOT NULL DEFAULT 1,
            boss_active INTEGER NOT NULL DEFAULT 0,
            boss_timer REAL NOT NULL DEFAULT 0.0,
            kills_in_stage INTEGER NOT NULL DEFAULT 0,
            player_data TEXT NOT NULL,
            created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
            updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_or_create_user(telegram_id: int, username: str = None) -> int:
    """Mendapatkan user_id berdasarkan telegram_id, atau membuat user baru jika belum ada."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    if row:
        user_id = row['id']
        cursor.execute("UPDATE users SET last_login = strftime('%s', 'now'), username = ? WHERE id = ?", 
                       (username, user_id))
    else:
        cursor.execute("INSERT INTO users (telegram_id, username) VALUES (?, ?)", 
                       (telegram_id, username))
        user_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return user_id

def load_game_state(user_id: int) -> dict | None:
    """Memuat state game untuk user_id tertentu dari database."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sector, substage, boss_active, boss_timer, kills_in_stage, player_data
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
            "user_id": user_id,
        }
    return None

def save_game_state(user_id: int, state: dict) -> None:
    """Menyimpan state game untuk user_id tertentu ke database."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # state['player'] sudah berupa dict dari save_manager.py
    player_data = state['player']
    player_json = json.dumps(player_data)
    
    cursor.execute("""
        INSERT INTO game_state (user_id, sector, substage, boss_active, boss_timer, kills_in_stage, player_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            sector = excluded.sector,
            substage = excluded.substage,
            boss_active = excluded.boss_active,
            boss_timer = excluded.boss_timer,
            kills_in_stage = excluded.kills_in_stage,
            player_data = excluded.player_data,
            updated_at = strftime('%s', 'now')
    """, (
        user_id,
        state.get('sector', 1),
        state.get('substage', 1),
        int(state.get('boss_active', False)),
        state.get('boss_timer', 0.0),
        state.get('kills_in_stage', 0),
        player_json
    ))
    
    conn.commit()
    conn.close()

def migrate_json_to_db():
    """Migrasi data dari savegame.json lama ke database (hanya untuk user default)."""
    json_path = Path("saves/savegame.json")
    if not json_path.exists():
        print("No legacy savegame.json found. Skipping migration.")
        return

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print("Legacy save file corrupted. Skipping migration.")
        return

    # Buat user dummy untuk migrasi
    legacy_telegram_id = 0  # Bisa diganti dengan ID Telegram admin
    user_id = get_or_create_user(legacy_telegram_id, "legacy_user")

    # Konversi data lama ke format state game baru
    old_stage = data.get('current_stage', 1)
    sector = ((old_stage - 1) // 10) + 1
    substage = ((old_stage - 1) % 10) + 1

    state = {
        'sector': sector,
        'substage': substage,
        'boss_active': data.get('boss_active', False),
        'boss_timer': data.get('boss_timer', 0.0),
        'kills_in_stage': data.get('kills_in_stage', 0),
        'player': data.get('player', {}),  # Ini perlu diubah ke objek Player yang sesungguhnya
    }
    # Perlu mengonversi player_data ke objek Player yang sesungguhnya
    # Untuk sementara, kita simpan sebagai dict dan biarkan save_manager yang menangani
    # (Ini adalah pekerjaan rumah untuk fase berikutnya)

    save_game_state(user_id, state)
    print(f"Migrated legacy save data to user {user_id}")

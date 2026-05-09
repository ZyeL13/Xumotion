from __future__ import annotations
from dataclasses import dataclass, field
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.player import Player
    from models.enemy import Enemy


@dataclass
class GameState:
    player: Player
    enemy: Enemy
    sector: int = 1                # <-- ganti current_stage
    substage: int = 1              # 1..10 (10 = boss)
    boss_active: bool = False
    boss_timer: float = 0.0        # detik tersisa saat boss fight
    user_id: int = 0
    kills_in_stage: int = 0
    last_save: float = 0.0
    running: bool = True
    offline_message: str = ""
    output_message: str = ""
    lock: threading.RLock = field(default_factory=threading.RLock)
    player_dead: bool = False
    # prime_timer dihapus

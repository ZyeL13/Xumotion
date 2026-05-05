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
    current_stage: int = 1
    kills_in_stage: int = 0
    last_save: float = 0.0
    running: bool = True
    offline_message: str = ""
    output_message: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)
    player_dead: bool = False
    prime_timer: float = 0.0

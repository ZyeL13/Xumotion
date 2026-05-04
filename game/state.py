from dataclasses import dataclass, field
from models.player import Player
from models.enemy import Enemy
import threading


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

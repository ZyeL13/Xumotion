# File: game/save_manager.py
# (refactored to use UserStateManager – only used internally by the manager)
from typing import Optional
from models.player import Player
from models.enemy import Enemy
from game.state import GameState


def load_game(user_id: int) -> Optional[GameState]:
    """Old interface kept for compatibility; now delegates to state_manager.
       Prefer using state_manager.load_or_create(telegram_id) directly."""
    from game.state_manager import state_manager
    # This is a fallback; the caller should use state_manager.load_or_create
    # with the real Telegram ID instead of user_id.
    return state_manager.load_or_create(telegram_id=user_id)  # type: ignore


def save_game(state: GameState, user_id: int = None) -> None:
    # This function is deprecated; use state_manager.save(state) directly.
    pass




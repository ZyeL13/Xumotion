import queue
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class GameEvent:
    timestamp: float
    event_type: str
    message: str


class EventLogger:
    def __init__(self):
        self._queue = queue.Queue()

    def emit(self, event_type: str, message: str):
        self._queue.put(GameEvent(time.time(), event_type, message))

    def poll(self, timeout: float = 0.1) -> Optional[GameEvent]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def clear(self):
        while self.poll():
            pass

event_logger = EventLogger()

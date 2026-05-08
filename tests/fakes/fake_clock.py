from datetime import datetime
import uuid

from app.ports.clock import Clock, IdGenerator


class FakeClock(Clock):
    def __init__(self, fixed: datetime):
        self._now = fixed

    def now(self) -> datetime:
        return self._now

    def set(self, dt: datetime) -> None:
        self._now = dt


class FakeIdGenerator(IdGenerator):
    def __init__(self, prefix: str = "test"):
        self._counter = 0
        self._prefix = prefix

    def generate(self) -> str:
        self._counter += 1
        return f"{self._prefix}-{self._counter}"

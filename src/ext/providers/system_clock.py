import uuid
from datetime import datetime

from app.ports.clock import Clock, IdGenerator


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now()


class UuidIdGenerator(IdGenerator):
    def generate(self) -> str:
        return uuid.uuid4().hex[:12]

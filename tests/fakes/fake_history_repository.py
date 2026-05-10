from datetime import datetime, timedelta

from app.domain.entities import ChatMessage
from app.ports.history_repository import HistoryRepository


class FakeHistoryRepository(HistoryRepository):
    def __init__(self):
        self._store: list[tuple[str, ChatMessage]] = []

    async def save(self, project_id: str, message: ChatMessage) -> None:
        self._store.append((project_id, message))

    async def get_context_around(
        self,
        project_id: str,
        anchor: datetime,
        max_messages: int,
        before_minutes: int,
        after_minutes: int,
    ) -> list[ChatMessage]:
        before_cutoff = anchor - timedelta(minutes=before_minutes)
        after_cutoff = anchor + timedelta(minutes=after_minutes)
        matches = [
            msg for pid, msg in self._store
            if pid == project_id
            and before_cutoff <= msg.timestamp <= after_cutoff
        ]
        matches.sort(key=lambda m: m.timestamp)
        return matches[:max_messages]

    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]:
        return [msg for pid, msg in self._store if pid == project_id]

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
        before: list[ChatMessage] = []
        at_anchor: list[ChatMessage] = []
        after: list[ChatMessage] = []
        for pid, msg in self._store:
            if pid != project_id:
                continue
            if before_cutoff <= msg.timestamp < anchor:
                before.append(msg)
            elif msg.timestamp == anchor:
                at_anchor.append(msg)
            elif anchor < msg.timestamp <= after_cutoff:
                after.append(msg)
        before.sort(key=lambda m: m.timestamp)
        at_anchor.sort(key=lambda m: m.timestamp)
        after.sort(key=lambda m: m.timestamp)
        return before[-max_messages:] + at_anchor + after[:max_messages]

    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]:
        return [msg for pid, msg in self._store if pid == project_id]

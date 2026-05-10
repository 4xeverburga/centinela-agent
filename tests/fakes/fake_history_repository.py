from datetime import datetime, timedelta

from app.domain.entities import ChatMessage
from app.ports.history_repository import HistoryRepository


class FakeHistoryRepository(HistoryRepository):
    def __init__(self):
        self._store: list[tuple[str, ChatMessage]] = []

    async def save(self, project_id: str, message: ChatMessage) -> None:
        self._store.append((project_id, message))

    async def get_by_message_id(self, project_id: str, message_id: int) -> ChatMessage | None:
        for pid, msg in self._store:
            if pid == project_id and msg.message_id == message_id:
                return msg
        return None

    async def get_context_around(
        self,
        project_id: str,
        anchor: ChatMessage,
        max_messages: int,
        before_minutes: int,
        after_minutes: int,
    ) -> list[ChatMessage]:
        before_cutoff = anchor.timestamp - timedelta(minutes=before_minutes)
        after_cutoff = anchor.timestamp + timedelta(minutes=after_minutes)
        before: list[ChatMessage] = []
        after: list[ChatMessage] = []
        for pid, msg in self._store:
            if pid != project_id:
                continue
            if before_cutoff <= msg.timestamp and msg.message_id < anchor.message_id:
                before.append(msg)
            elif msg.timestamp <= after_cutoff and msg.message_id > anchor.message_id:
                after.append(msg)
        before.sort(key=lambda m: m.message_id)
        after.sort(key=lambda m: m.message_id)
        return before[-max_messages:] + [anchor] + after[:max_messages]

    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]:
        return [msg for pid, msg in self._store if pid == project_id]

    async def get_caption_in_cluster(self, project_id: str, cluster_id: str) -> str:
        for pid, msg in self._store:
            if pid == project_id and msg.cluster_id == cluster_id and msg.text:
                return msg.text
        return ""

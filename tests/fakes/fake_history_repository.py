from datetime import datetime, timedelta

from app.domain.entities import ChatMessage
from app.ports.history_repository import HistoryRepository


class FakeHistoryRepository(HistoryRepository):
    def __init__(self):
        self._store: list[tuple[str, ChatMessage]] = []

    async def save(self, project_id: str, message: ChatMessage) -> None:
        self._store.append((project_id, message))

    async def get_recent_for_user(
        self, project_id: str, telegram_user_id: str, max_messages: int, window_minutes: int
    ) -> list[ChatMessage]:
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        result = []
        for pid, msg in reversed(self._store):
            if pid != project_id:
                continue
            if telegram_user_id and msg.telegram_user_id != telegram_user_id:
                continue
            if msg.timestamp < cutoff:
                break
            result.append(msg)
            if len(result) >= max_messages:
                break
        return list(reversed(result))

    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]:
        return [msg for pid, msg in self._store if pid == project_id]

from abc import ABC, abstractmethod

from app.domain.entities import ChatMessage


class HistoryRepository(ABC):
    @abstractmethod
    async def save(self, project_id: str, message: ChatMessage) -> None: ...

    @abstractmethod
    async def get_recent_for_user(
        self, project_id: str, telegram_user_id: str, max_messages: int, window_minutes: int
    ) -> list[ChatMessage]: ...

    @abstractmethod
    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]: ...

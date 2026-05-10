from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities import ChatMessage


class HistoryRepository(ABC):
    @abstractmethod
    async def save(self, project_id: str, message: ChatMessage) -> None: ...

    @abstractmethod
    async def get_context_around(
        self,
        project_id: str,
        anchor: datetime,
        max_messages: int,
        before_minutes: int,
        after_minutes: int,
    ) -> list[ChatMessage]: ...

    @abstractmethod
    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]: ...

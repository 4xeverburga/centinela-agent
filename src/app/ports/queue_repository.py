from abc import ABC, abstractmethod

from app.domain.entities import QueueItem, QueueStatus


class QueueRepository(ABC):
    @abstractmethod
    async def save(self, item: QueueItem) -> None: ...

    @abstractmethod
    async def get_oldest_pending(self, project_id: str, min_age_seconds: int) -> QueueItem | None: ...

    @abstractmethod
    async def list_pending_in_window(
        self, project_id: str, window_seconds: int
    ) -> list[QueueItem]: ...

    @abstractmethod
    async def update_status(
        self,
        file_id: str,
        system_version: str,
        status: QueueStatus,
        attempts: int,
        last_error: str,
        worker_id: str,
    ) -> None: ...

    @abstractmethod
    async def mark_completed(self, file_id: str, system_version: str, processed_at: str) -> None: ...

    @abstractmethod
    async def get_by_key(self, file_id: str, system_version: str) -> QueueItem | None: ...

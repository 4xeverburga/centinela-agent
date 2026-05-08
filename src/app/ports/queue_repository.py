from abc import ABC, abstractmethod

from app.domain.entities import QueueItem, QueueStatus


class QueueRepository(ABC):
    @abstractmethod
    async def save(self, item: QueueItem) -> int: ...

    @abstractmethod
    async def get_oldest_pending(self, project_id: str) -> QueueItem | None: ...

    @abstractmethod
    async def list_pending_in_window(
        self, project_id: str, window_seconds: int
    ) -> list[QueueItem]: ...

    @abstractmethod
    async def update_status(
        self,
        item_id: int,
        status: QueueStatus,
        attempts: int,
        last_error: str,
        worker_id: str,
    ) -> None: ...

    @abstractmethod
    async def mark_completed(self, item_id: int, processed_at: str) -> None: ...

    @abstractmethod
    async def mark_cluster(
        self, item_id: int, cluster_id: str, is_representative: bool, sharpness_score: float
    ) -> None: ...

    @abstractmethod
    async def get_by_id(self, item_id: int) -> QueueItem | None: ...

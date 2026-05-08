from app.domain.entities import QueueItem, QueueStatus
from app.ports.queue_repository import QueueRepository


class FakeQueueRepository(QueueRepository):
    def __init__(self):
        self._store: dict[int, QueueItem] = {}
        self._counter = 0

    async def save(self, item: QueueItem) -> int:
        self._counter += 1
        from dataclasses import replace
        stored = replace(item, id=self._counter)
        self._store[self._counter] = stored
        return self._counter

    async def get_oldest_pending(self, project_id: str) -> QueueItem | None:
        pending = [
            i for i in self._store.values()
            if i.project_id == project_id and i.status == QueueStatus.PENDING
        ]
        if not pending:
            return None
        return min(pending, key=lambda x: x.received_at)

    async def list_pending_in_window(
        self, project_id: str, window_seconds: int
    ) -> list[QueueItem]:
        return [
            i for i in self._store.values()
            if i.project_id == project_id and i.status == QueueStatus.PENDING
        ]

    async def update_status(
        self, item_id: int, status: QueueStatus, attempts: int, last_error: str, worker_id: str
    ) -> None:
        from dataclasses import replace
        item = self._store[item_id]
        self._store[item_id] = replace(
            item, status=status, attempts=attempts, last_error=last_error, worker_id=worker_id
        )

    async def mark_completed(self, item_id: int, processed_at: str) -> None:
        from dataclasses import replace
        item = self._store[item_id]
        self._store[item_id] = replace(
            item, status=QueueStatus.COMPLETED, processed_at=processed_at
        )

    async def mark_cluster(
        self, item_id: int, cluster_id: str, is_representative: bool, sharpness_score: float
    ) -> None:
        from dataclasses import replace
        item = self._store[item_id]
        self._store[item_id] = replace(
            item, cluster_id=cluster_id, is_representative=is_representative,
            sharpness_score=sharpness_score,
        )

    async def get_by_id(self, item_id: int) -> QueueItem | None:
        return self._store.get(item_id)

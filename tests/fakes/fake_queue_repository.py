from app.domain.entities import QueueItem, QueueStatus
from app.ports.queue_repository import QueueRepository


class FakeQueueRepository(QueueRepository):
    def __init__(self):
        self._store: dict[str, QueueItem] = {}

    async def save(self, item: QueueItem) -> None:
        key = f"{item.file_id}:{item.system_version}"
        self._store[key] = item

    async def get_oldest_pending(self, project_id: str, min_age_seconds: int) -> QueueItem | None:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(seconds=min_age_seconds)
        pending = [
            i for i in self._store.values()
            if i.project_id == project_id and i.status == QueueStatus.PENDING
            and i.received_at <= cutoff
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
        self, file_id: str, system_version: str, status: QueueStatus,
        attempts: int, last_error: str, worker_id: str,
    ) -> None:
        from dataclasses import replace
        key = f"{file_id}:{system_version}"
        item = self._store[key]
        self._store[key] = replace(
            item, status=status, attempts=attempts, last_error=last_error, worker_id=worker_id
        )

    async def mark_completed(self, file_id: str, system_version: str, processed_at: str) -> None:
        from dataclasses import replace
        key = f"{file_id}:{system_version}"
        item = self._store[key]
        self._store[key] = replace(
            item, status=QueueStatus.COMPLETED, processed_at=processed_at
        )

    async def get_by_key(self, file_id: str, system_version: str) -> QueueItem | None:
        return self._store.get(f"{file_id}:{system_version}")

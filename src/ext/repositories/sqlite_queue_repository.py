from datetime import datetime

import aiosqlite

from app.domain.entities import QueueItem, QueueStatus
from app.ports.queue_repository import QueueRepository


class SqliteQueueRepository(QueueRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, item: QueueItem) -> None:
        await self._conn.execute(
            """INSERT INTO inspections_queue
               (file_id, system_version, project_id, chat_id, cluster_id,
                is_representative, status, attempts, received_at, last_error,
                worker_id, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.file_id, item.system_version, item.project_id, item.chat_id,
                item.cluster_id, int(item.is_representative), item.status.value,
                item.attempts, item.received_at.isoformat(), item.last_error,
                item.worker_id, item.processed_at,
            ),
        )
        await self._conn.commit()

    async def get_oldest_pending(self, project_id: str) -> QueueItem | None:
        cursor = await self._conn.execute(
            """SELECT * FROM inspections_queue
               WHERE project_id = ? AND status = 'PENDING'
               ORDER BY received_at ASC LIMIT 1""",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_item(row)

    async def list_pending_in_window(
        self, project_id: str, window_seconds: int
    ) -> list[QueueItem]:
        cursor = await self._conn.execute(
            """SELECT * FROM inspections_queue
               WHERE project_id = ? AND status = 'PENDING'
               ORDER BY received_at ASC""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_item(r) for r in rows]

    async def update_status(
        self, file_id: str, system_version: str, status: QueueStatus,
        attempts: int, last_error: str, worker_id: str,
    ) -> None:
        await self._conn.execute(
            """UPDATE inspections_queue
               SET status = ?, attempts = ?, last_error = ?, worker_id = ?
               WHERE file_id = ? AND system_version = ?""",
            (status.value, attempts, last_error, worker_id, file_id, system_version),
        )
        await self._conn.commit()

    async def mark_completed(self, file_id: str, system_version: str, processed_at: str) -> None:
        await self._conn.execute(
            """UPDATE inspections_queue
               SET status = 'COMPLETED', processed_at = ?
               WHERE file_id = ? AND system_version = ?""",
            (processed_at, file_id, system_version),
        )
        await self._conn.commit()

    async def get_by_key(self, file_id: str, system_version: str) -> QueueItem | None:
        cursor = await self._conn.execute(
            "SELECT * FROM inspections_queue WHERE file_id = ? AND system_version = ?",
            (file_id, system_version),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_item(row)

    @staticmethod
    def _row_to_item(row: aiosqlite.Row) -> QueueItem:
        return QueueItem(
            project_id=row["project_id"], file_id=row["file_id"],
            chat_id=row["chat_id"], system_version=row["system_version"],
            cluster_id=row["cluster_id"],
            is_representative=bool(row["is_representative"]),
            status=QueueStatus(row["status"]),
            attempts=row["attempts"],
            received_at=datetime.fromisoformat(row["received_at"]),
            last_error=row["last_error"], worker_id=row["worker_id"],
            processed_at=row["processed_at"],
        )

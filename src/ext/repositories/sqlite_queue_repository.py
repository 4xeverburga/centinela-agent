from datetime import datetime

import aiosqlite

from app.domain.entities import QueueItem, QueueStatus
from app.ports.queue_repository import QueueRepository


class SqliteQueueRepository(QueueRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, item: QueueItem) -> int:
        cursor = await self._conn.execute(
            """INSERT INTO queue
               (project_id, file_id, chat_id, cluster_id, is_representative,
                sharpness_score, status, attempts, received_at, last_error,
                worker_id, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.project_id,
                item.file_id,
                item.chat_id,
                item.cluster_id,
                int(item.is_representative),
                item.sharpness_score,
                item.status.value,
                item.attempts,
                item.received_at.isoformat(),
                item.last_error,
                item.worker_id,
                item.processed_at,
            ),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_oldest_pending(self, project_id: str) -> QueueItem | None:
        cursor = await self._conn.execute(
            """SELECT * FROM queue
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
            """SELECT * FROM queue
               WHERE project_id = ? AND status = 'PENDING'
               ORDER BY received_at ASC""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_item(r) for r in rows]

    async def update_status(
        self, item_id: int, status: QueueStatus, attempts: int, last_error: str, worker_id: str
    ) -> None:
        await self._conn.execute(
            "UPDATE queue SET status = ?, attempts = ?, last_error = ?, worker_id = ? WHERE id = ?",
            (status.value, attempts, last_error, worker_id, item_id),
        )
        await self._conn.commit()

    async def mark_completed(self, item_id: int, processed_at: str) -> None:
        await self._conn.execute(
            "UPDATE queue SET status = 'COMPLETED', processed_at = ? WHERE id = ?",
            (processed_at, item_id),
        )
        await self._conn.commit()

    async def mark_cluster(
        self, item_id: int, cluster_id: str, is_representative: bool, sharpness_score: float
    ) -> None:
        await self._conn.execute(
            """UPDATE queue SET cluster_id = ?, is_representative = ?, sharpness_score = ?
               WHERE id = ?""",
            (cluster_id, int(is_representative), sharpness_score, item_id),
        )
        await self._conn.commit()

    async def get_by_id(self, item_id: int) -> QueueItem | None:
        cursor = await self._conn.execute(
            "SELECT * FROM queue WHERE id = ?", (item_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_item(row)

    @staticmethod
    def _row_to_item(row: aiosqlite.Row) -> QueueItem:
        return QueueItem(
            id=row["id"],
            project_id=row["project_id"],
            file_id=row["file_id"],
            chat_id=row["chat_id"],
            cluster_id=row["cluster_id"],
            is_representative=bool(row["is_representative"]),
            sharpness_score=row["sharpness_score"],
            status=QueueStatus(row["status"]),
            attempts=row["attempts"],
            received_at=datetime.fromisoformat(row["received_at"]),
            last_error=row["last_error"],
            worker_id=row["worker_id"],
            processed_at=row["processed_at"],
        )

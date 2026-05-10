from datetime import datetime, timedelta

import aiosqlite

from app.domain.entities import ChatMessage, UserRole
from app.ports.history_repository import HistoryRepository


class SqliteHistoryRepository(HistoryRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, project_id: str, message: ChatMessage) -> None:
        await self._conn.execute(
            """INSERT INTO chat_history
               (project_id, telegram_user_id, display_name, role, text, file_id, cluster_id,
                timestamp, is_included_in_history, rejected_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                message.telegram_user_id,
                message.display_name,
                message.role.value,
                message.text,
                message.file_id,
                message.cluster_id,
                message.timestamp.isoformat(),
                int(message.is_included_in_history),
                message.rejected_reason,
            ),
        )
        await self._conn.commit()

    async def get_context_around(
        self,
        project_id: str,
        anchor: datetime,
        max_messages: int,
        before_minutes: int,
        after_minutes: int,
    ) -> list[ChatMessage]:
        anchor_iso = anchor.isoformat()
        before_cutoff = (anchor - timedelta(minutes=before_minutes)).isoformat()
        after_cutoff = (anchor + timedelta(minutes=after_minutes)).isoformat()

        cursor_before = await self._conn.execute(
            """SELECT * FROM chat_history
               WHERE project_id = ? AND is_included_in_history = 1
                 AND timestamp >= ? AND timestamp < ?
               ORDER BY timestamp DESC LIMIT ?""",
            (project_id, before_cutoff, anchor_iso, max_messages),
        )
        rows_before = await cursor_before.fetchall()

        cursor_anchor = await self._conn.execute(
            """SELECT * FROM chat_history
               WHERE project_id = ? AND is_included_in_history = 1
                 AND timestamp = ?
               ORDER BY rowid ASC""",
            (project_id, anchor_iso),
        )
        rows_anchor = await cursor_anchor.fetchall()

        cursor_after = await self._conn.execute(
            """SELECT * FROM chat_history
               WHERE project_id = ? AND is_included_in_history = 1
                 AND timestamp > ? AND timestamp <= ?
               ORDER BY timestamp ASC LIMIT ?""",
            (project_id, anchor_iso, after_cutoff, max_messages),
        )
        rows_after = await cursor_after.fetchall()

        return (
            [self._row_to_message(r) for r in reversed(rows_before)]
            + [self._row_to_message(r) for r in rows_anchor]
            + [self._row_to_message(r) for r in rows_after]
        )

    async def get_all_for_project(self, project_id: str) -> list[ChatMessage]:
        cursor = await self._conn.execute(
            "SELECT * FROM chat_history WHERE project_id = ? ORDER BY timestamp ASC",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_message(r) for r in rows]

    @staticmethod
    def _row_to_message(row: aiosqlite.Row) -> ChatMessage:
        return ChatMessage(
            telegram_user_id=row["telegram_user_id"],
            display_name=row["display_name"],
            role=UserRole(row["role"]),
            text=row["text"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            file_id=row["file_id"],
            cluster_id=row["cluster_id"],
            is_included_in_history=bool(row["is_included_in_history"]),
            rejected_reason=row["rejected_reason"],
        )

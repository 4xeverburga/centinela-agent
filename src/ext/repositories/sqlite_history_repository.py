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
               (project_id, chat_id, message_id, telegram_user_id, display_name, role, text,
                file_id, cluster_id, timestamp, is_included_in_history, rejected_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                message.chat_id,
                message.message_id,
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

    async def get_by_message_id(self, project_id: str, message_id: int) -> ChatMessage | None:
        cursor = await self._conn.execute(
            "SELECT * FROM chat_history WHERE project_id = ? AND message_id = ?",
            (project_id, message_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_message(row)

    async def get_context_around(
        self,
        project_id: str,
        anchor: ChatMessage,
        max_messages: int,
        before_minutes: int,
        after_minutes: int,
    ) -> list[ChatMessage]:
        before_cutoff = (anchor.timestamp - timedelta(minutes=before_minutes)).isoformat()
        after_cutoff = (anchor.timestamp + timedelta(minutes=after_minutes)).isoformat()

        cursor_before = await self._conn.execute(
            """SELECT * FROM chat_history
               WHERE project_id = ? AND is_included_in_history = 1
                 AND timestamp >= ? AND message_id < ?
               ORDER BY message_id DESC LIMIT ?""",
            (project_id, before_cutoff, anchor.message_id, max_messages),
        )
        rows_before = await cursor_before.fetchall()

        cursor_after = await self._conn.execute(
            """SELECT * FROM chat_history
               WHERE project_id = ? AND is_included_in_history = 1
                 AND timestamp <= ? AND message_id > ?
               ORDER BY message_id ASC LIMIT ?""",
            (project_id, after_cutoff, anchor.message_id, max_messages),
        )
        rows_after = await cursor_after.fetchall()

        return (
            [self._row_to_message(r) for r in reversed(rows_before)]
            + [anchor]
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
            chat_id=row["chat_id"],
            message_id=row["message_id"],
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

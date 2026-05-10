import aiosqlite

from app.ports.assistant_repository import AssistantRepository


class SqliteAssistantRepository(AssistantRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def is_assistant(self, telegram_user_id: str) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM assistants WHERE telegram_user_id = ?",
            (telegram_user_id,),
        )
        row = await cursor.fetchone()
        return row is not None

    async def get_admin_ids_for_assistant(self, telegram_user_id: str) -> list[str]:
        cursor = await self._conn.execute(
            "SELECT admin_user_id FROM assistants WHERE telegram_user_id = ?",
            (telegram_user_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def add(self, telegram_user_id: str, admin_user_id: str, added_at: str) -> None:
        await self._conn.execute(
            "INSERT OR IGNORE INTO assistants (telegram_user_id, admin_user_id, added_at) VALUES (?, ?, ?)",
            (telegram_user_id, admin_user_id, added_at),
        )
        await self._conn.commit()

    async def seed(self, entries: list[tuple[str, str]], added_at: str) -> None:
        for uid, admin_id in entries:
            await self._conn.execute(
                "INSERT OR IGNORE INTO assistants (telegram_user_id, admin_user_id, added_at) VALUES (?, ?, ?)",
                (uid, admin_id, added_at),
            )
        await self._conn.commit()

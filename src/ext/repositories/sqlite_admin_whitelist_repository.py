import aiosqlite

from app.ports.admin_whitelist_repository import AdminWhitelistRepository


class SqliteAdminWhitelistRepository(AdminWhitelistRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def is_admin(self, telegram_user_id: str) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM admin_whitelist WHERE telegram_user_id = ?",
            (telegram_user_id,),
        )
        row = await cursor.fetchone()
        return row is not None

    async def add(self, telegram_user_id: str, added_at: str) -> None:
        await self._conn.execute(
            "INSERT OR IGNORE INTO admin_whitelist (telegram_user_id, added_at) VALUES (?, ?)",
            (telegram_user_id, added_at),
        )
        await self._conn.commit()

    async def seed(self, telegram_user_ids: list[str], added_at: str) -> None:
        for uid in telegram_user_ids:
            await self._conn.execute(
                "INSERT OR IGNORE INTO admin_whitelist (telegram_user_id, added_at) VALUES (?, ?)",
                (uid, added_at),
            )
        await self._conn.commit()

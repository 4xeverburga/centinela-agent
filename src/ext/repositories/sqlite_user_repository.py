import aiosqlite

from app.domain.entities import User, UserRole
from app.ports.user_repository import UserRepository


class SqliteUserRepository(UserRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, user: User) -> None:
        await self._conn.execute(
            "INSERT INTO users (telegram_user_id, display_name, role) VALUES (?, ?, ?)",
            (user.telegram_user_id, user.display_name, user.role.value),
        )
        await self._conn.commit()

    async def get_by_id(self, telegram_user_id: str) -> User | None:
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return User(
            telegram_user_id=row["telegram_user_id"],
            display_name=row["display_name"],
            role=UserRole(row["role"]),
        )

    async def upsert(self, user: User) -> None:
        await self._conn.execute(
            """INSERT OR REPLACE INTO users (telegram_user_id, display_name, role)
               VALUES (?, ?, ?)""",
            (user.telegram_user_id, user.display_name, user.role.value),
        )
        await self._conn.commit()

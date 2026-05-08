from app.domain.entities import User
from app.ports.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self):
        self._store: dict[str, User] = {}

    async def save(self, user: User) -> None:
        self._store[user.telegram_user_id] = user

    async def get_by_id(self, telegram_user_id: str) -> User | None:
        return self._store.get(telegram_user_id)

    async def upsert(self, user: User) -> None:
        self._store[user.telegram_user_id] = user

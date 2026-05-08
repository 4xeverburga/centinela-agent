from abc import ABC, abstractmethod

from app.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_id(self, telegram_user_id: str) -> User | None: ...

    @abstractmethod
    async def upsert(self, user: User) -> None: ...

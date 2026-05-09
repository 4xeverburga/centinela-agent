from abc import ABC, abstractmethod


class AdminWhitelistRepository(ABC):
    @abstractmethod
    async def is_admin(self, telegram_user_id: str) -> bool: ...

    @abstractmethod
    async def add(self, telegram_user_id: str, added_at: str) -> None: ...

    @abstractmethod
    async def seed(self, telegram_user_ids: list[str], added_at: str) -> None: ...

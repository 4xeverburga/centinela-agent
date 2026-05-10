from abc import ABC, abstractmethod


class AssistantRepository(ABC):
    @abstractmethod
    async def is_assistant(self, telegram_user_id: str) -> bool: ...

    @abstractmethod
    async def get_admin_ids_for_assistant(self, telegram_user_id: str) -> list[str]: ...

    @abstractmethod
    async def add(self, telegram_user_id: str, admin_user_id: str, added_at: str) -> None: ...

    @abstractmethod
    async def seed(self, entries: list[tuple[str, str]], added_at: str) -> None: ...

from abc import ABC, abstractmethod

from app.domain.entities import InspectionRecord


class InspectionRepository(ABC):
    @abstractmethod
    async def save(self, record: InspectionRecord) -> int: ...

    @abstractmethod
    async def get_recent_for_project(
        self, project_id: str, limit: int
    ) -> list[InspectionRecord]: ...

    @abstractmethod
    async def get_all_for_project(self, project_id: str) -> list[InspectionRecord]: ...

    @abstractmethod
    async def update_validated(self, record_id: int, validated_by_admin: bool) -> None: ...

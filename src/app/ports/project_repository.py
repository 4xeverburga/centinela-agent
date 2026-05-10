from abc import ABC, abstractmethod

from app.domain.entities import Project, ProjectStatus


class ProjectRepository(ABC):
    @abstractmethod
    async def save(self, project: Project) -> None: ...

    @abstractmethod
    async def get_by_id(self, project_id: str) -> Project | None: ...

    @abstractmethod
    async def get_active_by_chat(self, chat_id: str) -> Project | None: ...

    @abstractmethod
    async def list_by_status(self, status: ProjectStatus) -> list[Project]: ...

    @abstractmethod
    async def update_status(
        self,
        project_id: str,
        status: ProjectStatus,
        closure_reason: str | None,
    ) -> None: ...

from datetime import datetime

from app.domain.entities import Project, ProjectStatus
from app.ports.project_repository import ProjectRepository


class FakeProjectRepository(ProjectRepository):
    def __init__(self):
        self._store: dict[str, Project] = {}

    async def save(self, project: Project) -> None:
        self._store[project.project_id] = project

    async def get_by_id(self, project_id: str) -> Project | None:
        return self._store.get(project_id)

    async def get_active_by_chat(self, chat_id: str) -> Project | None:
        for p in self._store.values():
            if p.chat_id == chat_id and p.status == ProjectStatus.ACTIVE:
                return p
        return None

    async def list_by_status(self, status: ProjectStatus) -> list[Project]:
        return [p for p in self._store.values() if p.status == status]

    async def update_status(
        self, project_id: str, status: ProjectStatus, closure_reason: str | None
    ) -> None:
        from dataclasses import replace
        p = self._store[project_id]
        self._store[project_id] = replace(
            p, status=status, closure_reason=closure_reason or ""
        )

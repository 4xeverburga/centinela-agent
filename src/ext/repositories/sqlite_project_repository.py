from datetime import datetime

import aiosqlite

from app.domain.entities import Project, ProjectStatus
from app.ports.project_repository import ProjectRepository


class SqliteProjectRepository(ProjectRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, project: Project) -> None:
        await self._conn.execute(
            """INSERT OR REPLACE INTO projects
               (project_id, chat_id, local_name, admin_user_id, status,
                started_at, floor_plan_file_id, finished_at, closure_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project.project_id,
                project.chat_id,
                project.local_name,
                project.admin_user_id,
                project.status.value,
                project.started_at.isoformat(),
                project.floor_plan_file_id,
                project.finished_at,
                project.closure_reason,
            ),
        )
        await self._conn.commit()

    async def get_by_id(self, project_id: str) -> Project | None:
        cursor = await self._conn.execute(
            "SELECT * FROM projects WHERE project_id = ?", (project_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_project(row)

    async def get_active_by_chat(self, chat_id: str) -> Project | None:
        cursor = await self._conn.execute(
            "SELECT * FROM projects WHERE chat_id = ? AND status = 'ACTIVE'", (chat_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_project(row)

    async def list_by_status(self, status: ProjectStatus) -> list[Project]:
        cursor = await self._conn.execute(
            "SELECT * FROM projects WHERE status = ?", (status.value,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_project(r) for r in rows]

    async def update_status(
        self, project_id: str, status: ProjectStatus, closure_reason: str | None
    ) -> None:
        await self._conn.execute(
            "UPDATE projects SET status = ?, closure_reason = ? WHERE project_id = ?",
            (status.value, closure_reason or "", project_id),
        )
        await self._conn.commit()

    @staticmethod
    def _row_to_project(row: aiosqlite.Row) -> Project:
        return Project(
            project_id=row["project_id"],
            chat_id=row["chat_id"],
            local_name=row["local_name"],
            admin_user_id=row["admin_user_id"],
            status=ProjectStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            floor_plan_file_id=row["floor_plan_file_id"],
            finished_at=row["finished_at"],
            closure_reason=row["closure_reason"],
        )

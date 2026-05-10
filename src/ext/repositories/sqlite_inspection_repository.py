from datetime import datetime

import aiosqlite

from app.domain.entities import InspectionRecord, InspectionStatus
from app.ports.inspection_repository import InspectionRepository


class SqliteInspectionRepository(InspectionRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, record: InspectionRecord) -> int:
        cursor = await self._conn.execute(
            """INSERT INTO inspections
               (project_id, image_file_id, system_version, item_id, category,
                inspection_status, location_on_map, ocr_data, tech_observation,
                ai_system_observation, is_suspicious, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.project_id,
                record.image_file_id,
                record.system_version,
                record.item_id,
                record.category,
                record.inspection_status.value,
                record.location_on_map,
                record.ocr_data,
                record.tech_observation,
                record.ai_system_observation,
                int(record.is_suspicious),
                record.created_at.isoformat(),
            ),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_recent_for_project(
        self, project_id: str, limit: int
    ) -> list[InspectionRecord]:
        cursor = await self._conn.execute(
            """SELECT * FROM inspections WHERE project_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(r) for r in rows]

    async def get_all_for_project(self, project_id: str) -> list[InspectionRecord]:
        cursor = await self._conn.execute(
            "SELECT * FROM inspections WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(r) for r in rows]

    async def get_pending_suspicious(
        self, project_id: str, limit: int
    ) -> list[InspectionRecord]:
        cursor = await self._conn.execute(
            """SELECT i.* FROM inspections i
               WHERE i.project_id = ? AND i.is_suspicious = 1
                 AND NOT EXISTS (
                     SELECT 1 FROM human_reviews hr
                     WHERE hr.image_file_id = i.image_file_id AND hr.answer != ''
                 )
               ORDER BY i.created_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(r) for r in rows]

    async def get_by_image_file_id(self, file_id: str) -> InspectionRecord | None:
        cursor = await self._conn.execute(
            "SELECT * FROM inspections WHERE image_file_id = ? ORDER BY created_at DESC LIMIT 1",
            (file_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_record(row) if row else None

    @staticmethod
    def _row_to_record(row: aiosqlite.Row) -> InspectionRecord:
        return InspectionRecord(
            id=row["id"],
            project_id=row["project_id"],
            image_file_id=row["image_file_id"],
            system_version=row["system_version"],
            item_id=row["item_id"],
            category=row["category"],
            inspection_status=InspectionStatus(row["inspection_status"]),
            location_on_map=row["location_on_map"],
            ocr_data=row["ocr_data"],
            tech_observation=row["tech_observation"],
            ai_system_observation=row["ai_system_observation"],
            is_suspicious=bool(row["is_suspicious"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

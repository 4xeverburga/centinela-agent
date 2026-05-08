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
               (project_id, queue_id, image_file_id, item_id, category,
                inspection_status, location_on_map, ocr_data, tech_observation,
                ai_system_observation, is_suspicious, validated_by_admin,
                created_at, anomaly_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.project_id,
                record.queue_id,
                record.image_file_id,
                record.item_id,
                record.category,
                record.inspection_status.value,
                record.location_on_map,
                record.ocr_data,
                record.tech_observation,
                record.ai_system_observation,
                int(record.is_suspicious),
                int(record.validated_by_admin),
                record.created_at.isoformat(),
                record.anomaly_reason,
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

    async def update_validated(self, record_id: int, validated_by_admin: bool) -> None:
        await self._conn.execute(
            "UPDATE inspections SET validated_by_admin = ? WHERE id = ?",
            (int(validated_by_admin), record_id),
        )
        await self._conn.commit()

    @staticmethod
    def _row_to_record(row: aiosqlite.Row) -> InspectionRecord:
        return InspectionRecord(
            id=row["id"],
            project_id=row["project_id"],
            queue_id=row["queue_id"],
            image_file_id=row["image_file_id"],
            item_id=row["item_id"],
            category=row["category"],
            inspection_status=InspectionStatus(row["inspection_status"]),
            location_on_map=row["location_on_map"],
            ocr_data=row["ocr_data"],
            tech_observation=row["tech_observation"],
            ai_system_observation=row["ai_system_observation"],
            is_suspicious=bool(row["is_suspicious"]),
            validated_by_admin=bool(row["validated_by_admin"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            anomaly_reason=row["anomaly_reason"],
        )

from app.domain.entities import InspectionRecord
from app.ports.inspection_repository import InspectionRepository


class FakeInspectionRepository(InspectionRepository):
    def __init__(self):
        self._store: dict[str, InspectionRecord] = {}

    async def save(self, record: InspectionRecord) -> None:
        key = f"{record.chat_id}:{record.message_id}:{record.system_version}"
        self._store[key] = record

    async def get_recent_for_project(
        self, project_id: str, limit: int
    ) -> list[InspectionRecord]:
        matches = [r for r in self._store.values() if r.project_id == project_id]
        matches.sort(key=lambda r: r.created_at, reverse=True)
        return matches[:limit]

    async def get_all_for_project(self, project_id: str) -> list[InspectionRecord]:
        return [r for r in self._store.values() if r.project_id == project_id]

    async def get_pending_suspicious(
        self, project_id: str, limit: int
    ) -> list[InspectionRecord]:
        return [
            r for r in self._store.values()
            if r.project_id == project_id and r.is_suspicious
        ][:limit]

    async def get_by_image_file_id(self, file_id: str) -> InspectionRecord | None:
        for r in self._store.values():
            if r.image_file_id == file_id:
                return r
        return None

from app.domain.entities import InspectionRecord
from app.ports.inspection_repository import InspectionRepository


class FakeInspectionRepository(InspectionRepository):
    def __init__(self):
        self._store: dict[int, InspectionRecord] = {}
        self._counter = 0

    async def save(self, record: InspectionRecord) -> int:
        self._counter += 1
        from dataclasses import replace
        stored = replace(record, id=self._counter)
        self._store[self._counter] = stored
        return self._counter

    async def get_recent_for_project(
        self, project_id: str, limit: int
    ) -> list[InspectionRecord]:
        matches = [r for r in self._store.values() if r.project_id == project_id]
        matches.sort(key=lambda r: r.created_at, reverse=True)
        return matches[:limit]

    async def get_all_for_project(self, project_id: str) -> list[InspectionRecord]:
        return [r for r in self._store.values() if r.project_id == project_id]

    async def update_validated(self, record_id: int, validated_by_admin: bool) -> None:
        from dataclasses import replace
        r = self._store[record_id]
        self._store[record_id] = replace(r, validated_by_admin=validated_by_admin)

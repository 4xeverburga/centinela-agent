from datetime import datetime

from app.domain.entities import (
    ChatMessage,
    ImagePayload,
    InspectionRecord,
    InspectionStatus,
)
from app.ports.llm_inspector import LLMInspector


class FakeLLMInspector(LLMInspector):
    def __init__(self, suspicious: bool = False):
        self._suspicious = suspicious

    async def inspect(
        self,
        image: ImagePayload,
        floor_plan_image: bytes,
        chat_window: list[ChatMessage],
        inspections_by_file_id: dict[str, dict],
        chat_id: str,
        message_id: int,
        project_id: str,
        system_version: str,
        image_file_id: str,
    ) -> InspectionRecord:
        return InspectionRecord(
            chat_id=chat_id,
            message_id=message_id,
            system_version=system_version,
            project_id=project_id,
            image_file_id=image_file_id,
            item_id="ITEM-001",
            category="CCTV",
            inspection_status=InspectionStatus.DURANTE,
            location_on_map="Zona A",
            ocr_data="SN-12345",
            tech_observation="",
            ai_system_observation="Cambio de categoría" if self._suspicious else "",
            is_suspicious=self._suspicious,
            created_at=datetime.now(),
        )

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
        recent_inspections_json: list[dict],
        project_id: str,
        queue_id: int,
        image_file_id: str,
    ) -> InspectionRecord:
        return InspectionRecord(
            project_id=project_id,
            queue_id=queue_id,
            image_file_id=image_file_id,
            item_id="ITEM-001",
            category="CCTV",
            inspection_status=InspectionStatus.DURANTE,
            location_on_map="Zona A",
            ocr_data="SN-12345",
            tech_observation="",
            ai_system_observation="",
            is_suspicious=self._suspicious,
            validated_by_admin=False,
            created_at=datetime.now(),
            anomaly_reason="Cambio de categoría" if self._suspicious else "",
        )

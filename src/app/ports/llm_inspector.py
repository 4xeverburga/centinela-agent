from abc import ABC, abstractmethod

from app.domain.entities import ChatMessage, ImagePayload, InspectionRecord


class LLMInspector(ABC):
    @abstractmethod
    async def inspect(
        self,
        image: ImagePayload,
        floor_plan_image: bytes,
        chat_window: list[ChatMessage],
        recent_inspections_json: list[dict],
        project_id: str,
        queue_id: int,
        image_file_id: str,
    ) -> InspectionRecord: ...

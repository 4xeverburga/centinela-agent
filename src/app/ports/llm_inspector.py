from abc import ABC, abstractmethod

from app.domain.entities import ChatMessage, ImagePayload, InspectionRecord


class LLMInspector(ABC):
    @abstractmethod
    async def inspect(
        self,
        image: ImagePayload,
        floor_plan_image: bytes,
        chat_window: list[ChatMessage],
        inspections_by_file_id: dict[str, dict],
        project_id: str,
        system_version: str,
        image_file_id: str,
    ) -> InspectionRecord: ...

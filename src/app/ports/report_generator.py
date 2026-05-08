from abc import ABC, abstractmethod

from app.domain.entities import ChatMessage, InspectionRecord, Project


class ReportGenerator(ABC):
    @abstractmethod
    async def generate(
        self,
        project: Project,
        inspections: list[InspectionRecord],
        chat_history: list[ChatMessage],
    ) -> str: ...

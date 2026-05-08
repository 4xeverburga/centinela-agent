from app.domain.entities import ChatMessage, InspectionRecord, Project
from app.ports.report_generator import ReportGenerator


class FakeReportGenerator(ReportGenerator):
    async def generate(
        self,
        project: Project,
        inspections: list[InspectionRecord],
        chat_history: list[ChatMessage],
    ) -> str:
        return f"# Reporte {project.project_id}\n\nInspecciones: {len(inspections)}\n"

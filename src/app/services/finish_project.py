from app.domain.entities import ProjectStatus
from app.ports.clock import Clock
from app.ports.project_repository import ProjectRepository
from app.ports.inspection_repository import InspectionRepository
from app.ports.history_repository import HistoryRepository
from app.ports.human_review_repository import HumanReviewRepository
from app.ports.report_generator import ReportGenerator
from app.ports.telegram_gateway import TelegramGateway


class FinishProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        inspection_repo: InspectionRepository,
        history_repo: HistoryRepository,
        review_repo: HumanReviewRepository,
        report_gen: ReportGenerator,
        telegram: TelegramGateway,
        clock: Clock,
    ):
        self._project_repo = project_repo
        self._inspection_repo = inspection_repo
        self._history_repo = history_repo
        self._review_repo = review_repo
        self._report_gen = report_gen
        self._telegram = telegram
        self._clock = clock

    async def execute(self, chat_id: str) -> str:
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            raise ValueError(f"No active project in chat {chat_id}")

        inspections = await self._inspection_repo.get_all_for_project(project.project_id)
        history = await self._history_repo.get_all_for_project(project.project_id)

        report_text = await self._report_gen.generate(project, inspections, history)

        await self._project_repo.update_status(
            project.project_id, ProjectStatus.CLOSED, "manual"
        )

        report_bytes = report_text.encode("utf-8")
        await self._telegram.send_document(
            chat_id, report_bytes, f"reporte_{project.project_id}.md"
        )
        await self._telegram.send_message(
            chat_id,
            f"Proyecto '{project.local_name}' finalizado. Reporte generado.",
        )
        return report_text

from dataclasses import replace

from app.domain.entities import Project
from app.ports.project_repository import ProjectRepository
from app.ports.telegram_gateway import TelegramGateway


class RegisterFloorplanService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        telegram: TelegramGateway,
    ):
        self._project_repo = project_repo
        self._telegram = telegram

    async def execute(self, chat_id: str, file_id: str) -> bool:
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            return False

        updated = replace(project, floor_plan_file_id=file_id)
        await self._project_repo.save(updated)
        await self._telegram.send_message(
            chat_id, "Plano registrado correctamente."
        )
        return True

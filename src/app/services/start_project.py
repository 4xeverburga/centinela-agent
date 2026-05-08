from app.domain.entities import Project, ProjectStatus
from app.ports.clock import Clock, IdGenerator
from app.ports.project_repository import ProjectRepository
from app.ports.user_repository import UserRepository
from app.ports.telegram_gateway import TelegramGateway
from app.domain.entities import User, UserRole


class StartProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        user_repo: UserRepository,
        telegram: TelegramGateway,
        clock: Clock,
        id_gen: IdGenerator,
    ):
        self._project_repo = project_repo
        self._user_repo = user_repo
        self._telegram = telegram
        self._clock = clock
        self._id_gen = id_gen

    async def execute(
        self,
        chat_id: str,
        local_name: str,
        admin_telegram_id: str,
        admin_display_name: str,
    ) -> Project:
        existing = await self._project_repo.get_active_by_chat(chat_id)
        if existing is not None:
            raise ValueError(f"Already an active project in chat {chat_id}: {existing.project_id}")

        await self._user_repo.upsert(
            User(
                telegram_user_id=admin_telegram_id,
                display_name=admin_display_name,
                role=UserRole.ADMIN,
            )
        )

        project = Project(
            project_id=self._id_gen.generate(),
            chat_id=chat_id,
            local_name=local_name,
            admin_user_id=admin_telegram_id,
            status=ProjectStatus.ACTIVE,
            started_at=self._clock.now(),
            floor_plan_file_id="",
            finished_at="",
            closure_reason="",
        )
        await self._project_repo.save(project)
        await self._telegram.send_message(
            chat_id,
            f"Proyecto '{local_name}' iniciado. ID: {project.project_id}",
        )
        return project

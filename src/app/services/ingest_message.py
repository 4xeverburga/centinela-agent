from app.domain.entities import ChatMessage, User, UserRole
from app.ports.clock import Clock
from app.ports.history_repository import HistoryRepository
from app.ports.project_repository import ProjectRepository
from app.ports.user_repository import UserRepository


class IngestMessageService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        history_repo: HistoryRepository,
        user_repo: UserRepository,
        clock: Clock,
    ):
        self._project_repo = project_repo
        self._history_repo = history_repo
        self._user_repo = user_repo
        self._clock = clock

    async def execute(
        self,
        chat_id: str,
        telegram_user_id: str,
        display_name: str,
        text: str,
        message_id: int,
    ) -> bool:
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            return False

        user = await self._user_repo.get_by_id(telegram_user_id)
        role = user.role if user is not None else UserRole.TECNICO

        await self._user_repo.upsert(
            User(telegram_user_id=telegram_user_id, display_name=display_name, role=role)
        )

        message = ChatMessage(
            chat_id=chat_id,
            message_id=message_id,
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            role=role,
            text=text,
            timestamp=self._clock.now(),
        )
        await self._history_repo.save(project.project_id, message)
        return True

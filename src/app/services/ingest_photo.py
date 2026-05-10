from app.domain.entities import ChatMessage, QueueItem, QueueStatus, UserRole
from app.ports.clock import Clock
from app.ports.history_repository import HistoryRepository
from app.ports.project_repository import ProjectRepository
from app.ports.queue_repository import QueueRepository
from app.ports.user_repository import UserRepository


class IngestPhotoService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        queue_repo: QueueRepository,
        history_repo: HistoryRepository,
        user_repo: UserRepository,
        clock: Clock,
    ):
        self._project_repo = project_repo
        self._queue_repo = queue_repo
        self._history_repo = history_repo
        self._user_repo = user_repo
        self._clock = clock

    async def execute(
        self, chat_id: str, file_id: str, telegram_user_id: str, display_name: str,
    ) -> int:
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            return -1

        user = await self._user_repo.get_by_id(telegram_user_id)
        role = user.role if user is not None else UserRole.TECNICO

        message = ChatMessage(
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            role=role,
            text="",
            timestamp=self._clock.now(),
            file_id=file_id,
        )
        await self._history_repo.save(project.project_id, message)

        item = QueueItem(
            project_id=project.project_id,
            file_id=file_id,
            chat_id=chat_id,
            cluster_id="",
            is_representative=True,
            sharpness_score=0.0,
            status=QueueStatus.PENDING,
            attempts=0,
            received_at=self._clock.now(),
            last_error="",
            worker_id="",
            processed_at="",
        )
        return await self._queue_repo.save(item)

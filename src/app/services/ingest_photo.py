from app.domain.entities import QueueItem, QueueStatus
from app.ports.clock import Clock
from app.ports.project_repository import ProjectRepository
from app.ports.queue_repository import QueueRepository


class IngestPhotoService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        queue_repo: QueueRepository,
        clock: Clock,
    ):
        self._project_repo = project_repo
        self._queue_repo = queue_repo
        self._clock = clock

    async def execute(self, chat_id: str, file_id: str) -> int:
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            return -1

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

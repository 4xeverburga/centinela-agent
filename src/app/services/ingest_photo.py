import logging

from app.domain.entities import ChatMessage, IngestResult, QueueItem, QueueStatus, UserRole
from app.ports.clock import Clock
from app.ports.history_repository import HistoryRepository
from app.ports.image_processor import ImageProcessor
from app.ports.project_repository import ProjectRepository
from app.ports.queue_repository import QueueRepository
from app.ports.telegram_gateway import TelegramGateway
from app.ports.user_repository import UserRepository

logger = logging.getLogger(__name__)


class IngestPhotoService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        queue_repo: QueueRepository,
        history_repo: HistoryRepository,
        user_repo: UserRepository,
        telegram: TelegramGateway,
        image_processor: ImageProcessor,
        clock: Clock,
        sharpness_min: float,
        system_version: str,
    ):
        self._project_repo = project_repo
        self._queue_repo = queue_repo
        self._history_repo = history_repo
        self._user_repo = user_repo
        self._telegram = telegram
        self._image_processor = image_processor
        self._clock = clock
        self._sharpness_min = sharpness_min
        self._system_version = system_version

    async def execute(
        self,
        chat_id: str,
        file_id: str,
        telegram_user_id: str,
        display_name: str,
        caption: str,
        cluster_id: str,
        message_id: int,
    ) -> IngestResult:
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            return IngestResult.NO_PROJECT

        user = await self._user_repo.get_by_id(telegram_user_id)
        role = user.role if user is not None else UserRole.TECNICO

        # Download and check sharpness before queueing
        from app.domain.entities import ImagePayload
        raw_bytes = await self._telegram.download_file(file_id)
        raw_payload = ImagePayload(data=raw_bytes, mime_type="image/jpeg", width=0, height=0)
        compressed = self._image_processor.compress(raw_payload)
        sharpness = self._image_processor.sharpness(compressed)

        if sharpness < self._sharpness_min:
            message = ChatMessage(
                chat_id=chat_id,
                message_id=message_id,
                telegram_user_id=telegram_user_id,
                display_name=display_name,
                role=role,
                text=caption,
                timestamp=self._clock.now(),
                file_id=file_id,
                cluster_id=cluster_id,
                is_included_in_history=False,
                rejected_reason="blurry",
            )
            await self._history_repo.save(project.project_id, message)
            logger.info("Image %s rejected: sharpness %.1f < %.1f", file_id, sharpness, self._sharpness_min)
            return IngestResult.REJECTED_BLURRY

        message = ChatMessage(
            chat_id=chat_id,
            message_id=message_id,
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            role=role,
            text=caption,
            timestamp=self._clock.now(),
            file_id=file_id,
            cluster_id=cluster_id,
        )
        await self._history_repo.save(project.project_id, message)

        item = QueueItem(
            project_id=project.project_id,
            file_id=file_id,
            chat_id=chat_id,
            system_version=self._system_version,
            message_id=message_id,
            cluster_id=cluster_id,
            is_representative=True,
            status=QueueStatus.PENDING,
            attempts=0,
            received_at=self._clock.now(),
            last_error="",
            worker_id="",
            processed_at="",
        )
        await self._queue_repo.save(item)
        return IngestResult.QUEUED

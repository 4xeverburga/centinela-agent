import logging
from types import ModuleType

from app.domain.entities import (
    HumanReviewRequest,
    QueueStatus,
    ReviewTrigger,
)
from app.ports.clock import Clock
from app.ports.history_repository import HistoryRepository
from app.ports.human_review_repository import HumanReviewRepository
from app.ports.image_processor import ImageProcessor
from app.ports.inspection_repository import InspectionRepository
from app.ports.llm_inspector import LLMInspector
from app.ports.project_repository import ProjectRepository
from app.ports.queue_repository import QueueRepository
from app.ports.telegram_gateway import TelegramGateway

logger = logging.getLogger(__name__)


class ProcessQueueItemService:
    def __init__(
        self,
        queue_repo: QueueRepository,
        project_repo: ProjectRepository,
        history_repo: HistoryRepository,
        inspection_repo: InspectionRepository,
        review_repo: HumanReviewRepository,
        telegram: TelegramGateway,
        image_processor: ImageProcessor,
        llm_inspector: LLMInspector,
        clock: Clock,
        locale: ModuleType,
        system_version: str,
        context_max_messages: int,
        context_window_before_minutes: int,
        context_window_after_minutes: int,
        max_attempts: int,
        backoff_base: float,
    ):
        self._queue_repo = queue_repo
        self._project_repo = project_repo
        self._history_repo = history_repo
        self._inspection_repo = inspection_repo
        self._review_repo = review_repo
        self._telegram = telegram
        self._image_processor = image_processor
        self._llm_inspector = llm_inspector
        self._clock = clock
        self._locale = locale
        self._system_version = system_version
        self._context_max_messages = context_max_messages
        self._context_window_before_minutes = context_window_before_minutes
        self._context_window_after_minutes = context_window_after_minutes
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base

    async def execute(self, chat_id: str, message_id: int, system_version: str) -> bool:
        item = await self._queue_repo.get_by_key(chat_id, message_id, system_version)
        if item is None or item.status != QueueStatus.PENDING:
            return False

        await self._queue_repo.update_status(
            chat_id, message_id, system_version, QueueStatus.PROCESSING, item.attempts + 1, "", "worker-0"
        )

        try:
            project = await self._project_repo.get_by_id(item.project_id)
            if project is None:
                await self._queue_repo.update_status(
                    chat_id, message_id, system_version, QueueStatus.FAILED,
                    item.attempts + 1, "project not found", "worker-0"
                )
                return False

            raw_bytes = await self._telegram.download_file(item.file_id)
            from app.domain.entities import ImagePayload
            raw_payload = ImagePayload(data=raw_bytes, mime_type="image/jpeg", width=0, height=0)
            compressed = self._image_processor.compress(raw_payload)

            floor_plan_bytes = b""
            if project.floor_plan_file_id:
                floor_plan_bytes = await self._telegram.download_file(project.floor_plan_file_id)

            anchor_msg = await self._history_repo.get_by_message_id(
                project.project_id, item.message_id,
            )
            if anchor_msg is None:
                await self._queue_repo.update_status(
                    chat_id, message_id, system_version, QueueStatus.FAILED,
                    item.attempts + 1, "anchor message not found", "worker-0"
                )
                return False

            chat_messages = await self._history_repo.get_context_around(
                project.project_id,
                anchor_msg,
                self._context_max_messages,
                self._context_window_before_minutes,
                self._context_window_after_minutes,
            )

            inspections_by_file_id: dict[str, dict] = {}
            for msg in chat_messages:
                if not msg.file_id or msg.file_id == item.file_id:
                    continue
                rec = await self._inspection_repo.get_by_image_file_id(msg.file_id)
                if rec and not rec.is_suspicious:
                    inspections_by_file_id[msg.file_id] = {
                        "category": rec.category,
                        "status": rec.inspection_status.value,
                        "location_ref": rec.location_on_map,
                        "tech_observation": rec.tech_observation,
                        "system_observation": rec.ai_system_observation,
                    }

            record = await self._llm_inspector.inspect(
                image=compressed,
                floor_plan_image=floor_plan_bytes,
                chat_window=chat_messages,
                inspections_by_file_id=inspections_by_file_id,
                chat_id=chat_id,
                message_id=message_id,
                project_id=project.project_id,
                system_version=self._system_version,
                image_file_id=item.file_id,
            )

            await self._inspection_repo.save(record)

            if record.is_suspicious:
                review = HumanReviewRequest(
                    project_id=project.project_id,
                    trigger=ReviewTrigger.SUSPICIOUS_CATEGORY,
                    question=f"Categoría sospechosa: {record.category}. {record.ai_system_observation}",
                    asked_at=self._clock.now(),
                    image_file_id=item.file_id,
                    answer="",
                    reviewer_user_id="",
                    answered_at="",
                )
                await self._review_repo.save(review)
                logger.info(
                    "Suspicious alert queued for project %s: %s",
                    project.project_id, record.category,
                )

            now_str = self._clock.now().isoformat()
            await self._queue_repo.mark_completed(chat_id, message_id, system_version, now_str)
            return True

        except Exception as exc:
            logger.exception("Error processing queue item chat_id=%s message_id=%s", chat_id, message_id)
            new_attempts = item.attempts + 1
            if new_attempts >= self._max_attempts:
                await self._queue_repo.update_status(
                    chat_id, message_id, system_version, QueueStatus.FAILED,
                    new_attempts, str(exc), "worker-0"
                )
            else:
                await self._queue_repo.update_status(
                    chat_id, message_id, system_version, QueueStatus.PENDING,
                    new_attempts, str(exc), "worker-0"
                )
            return False

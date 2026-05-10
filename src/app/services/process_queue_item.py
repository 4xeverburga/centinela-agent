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
from app.ports.image_embedder import ImageEmbedder
from app.ports.image_processor import ImageProcessor
from app.ports.clustering_engine import ClusteringEngine
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
        image_embedder: ImageEmbedder,
        clustering_engine: ClusteringEngine,
        llm_inspector: LLMInspector,
        clock: Clock,
        locale: ModuleType,
        sharpness_min: float,
        similarity_threshold: float,
        context_max_messages: int,
        context_window_minutes: int,
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
        self._image_embedder = image_embedder
        self._clustering_engine = clustering_engine
        self._llm_inspector = llm_inspector
        self._clock = clock
        self._locale = locale
        self._sharpness_min = sharpness_min
        self._similarity_threshold = similarity_threshold
        self._context_max_messages = context_max_messages
        self._context_window_minutes = context_window_minutes
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base

    async def execute(self, item_id: int) -> bool:
        item = await self._queue_repo.get_by_id(item_id)
        if item is None or item.status != QueueStatus.PENDING:
            return False

        await self._queue_repo.update_status(
            item_id, QueueStatus.PROCESSING, item.attempts + 1, "", "worker-0"
        )

        try:
            project = await self._project_repo.get_by_id(item.project_id)
            if project is None:
                await self._queue_repo.update_status(
                    item_id, QueueStatus.FAILED, item.attempts + 1, "project not found", "worker-0"
                )
                return False

            raw_bytes = await self._telegram.download_file(item.file_id)
            from app.domain.entities import ImagePayload

            raw_payload = ImagePayload(data=raw_bytes, mime_type="image/jpeg", width=0, height=0)
            compressed = self._image_processor.compress(raw_payload)
            sharpness = self._image_processor.sharpness(compressed)

            if sharpness < self._sharpness_min:
                await self._queue_repo.update_status(
                    item_id, QueueStatus.INSUFFICIENT_EVIDENCE,
                    item.attempts + 1, "below sharpness threshold", "worker-0"
                )
                review = HumanReviewRequest(
                    project_id=item.project_id,
                    trigger=ReviewTrigger.INSUFFICIENT_EVIDENCE,
                    question="La imagen está demasiado borrosa. Por favor, tome otra foto.",
                    asked_at=self._clock.now(),
                    queue_id=item_id,
                    answer="",
                    reviewer_user_id="",
                    answered_at="",
                )
                await self._review_repo.save(review)
                await self._telegram.send_message(
                    item.chat_id,
                    self._locale.BLURRY_IMAGE,
                )
                return False

            await self._queue_repo.mark_cluster(item_id, "", True, sharpness)

            floor_plan_bytes = b""
            if project.floor_plan_file_id:
                floor_plan_bytes = await self._telegram.download_file(project.floor_plan_file_id)

            recent_inspections = await self._inspection_repo.get_recent_for_project(
                project.project_id, 5
            )
            seen_file_ids: set[str] = {
                r.image_file_id for r in recent_inspections if not r.is_suspicious
            }
            recent_json = [
                {
                    "category": r.category,
                    "status": r.inspection_status.value,
                    "location_ref": r.location_on_map,
                    "tech_observation": r.tech_observation,
                    "system_observation": r.ai_system_observation,
                }
                for r in recent_inspections
                if not r.is_suspicious
            ]

            chat_messages = await self._history_repo.get_recent_for_user(
                project.project_id,
                "",
                self._context_max_messages,
                self._context_window_minutes,
            )

            # Resolve image messages in the chat window to their inspection records.
            # Only non-suspicious records are included; the current image is skipped.
            for msg in chat_messages:
                if not msg.file_id or msg.file_id == item.file_id:
                    continue
                if msg.file_id in seen_file_ids:
                    continue
                rec = await self._inspection_repo.get_by_image_file_id(msg.file_id)
                if rec and not rec.is_suspicious:
                    seen_file_ids.add(msg.file_id)
                    recent_json.append({
                        "category": rec.category,
                        "status": rec.inspection_status.value,
                        "location_ref": rec.location_on_map,
                        "tech_observation": rec.tech_observation,
                        "system_observation": rec.ai_system_observation,
                    })

            record = await self._llm_inspector.inspect(
                image=compressed,
                floor_plan_image=floor_plan_bytes,
                chat_window=chat_messages,
                recent_inspections_json=recent_json,
                project_id=project.project_id,
                queue_id=item_id,
                image_file_id=item.file_id,
            )

            await self._inspection_repo.save(record)

            if record.is_suspicious:
                review = HumanReviewRequest(
                    project_id=project.project_id,
                    trigger=ReviewTrigger.SUSPICIOUS_CATEGORY,
                    question=f"Categoría sospechosa: {record.category}. {record.ai_system_observation}",
                    asked_at=self._clock.now(),
                    queue_id=item_id,
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
            await self._queue_repo.mark_completed(item_id, now_str)
            return True

        except Exception as exc:
            logger.exception("Error processing queue item %s", item_id)
            new_attempts = item.attempts + 1
            if new_attempts >= self._max_attempts:
                await self._queue_repo.update_status(
                    item_id, QueueStatus.FAILED, new_attempts, str(exc), "worker-0"
                )
            else:
                await self._queue_repo.update_status(
                    item_id, QueueStatus.PENDING, new_attempts, str(exc), "worker-0"
                )
            return False

import asyncio
import logging

from app.ports.queue_repository import QueueRepository
from app.ports.project_repository import ProjectRepository
from app.domain.entities import ProjectStatus
from app.services.process_queue_item import ProcessQueueItemService

logger = logging.getLogger(__name__)


class QueueWorker:
    def __init__(
        self,
        queue_repo: QueueRepository,
        project_repo: ProjectRepository,
        process_service: ProcessQueueItemService,
        poll_interval_seconds: float,
        grace_period_seconds: int,
    ):
        self._queue_repo = queue_repo
        self._project_repo = project_repo
        self._process_service = process_service
        self._poll_interval = poll_interval_seconds
        self._grace_period = grace_period_seconds
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Queue worker started (poll every %.1fs)", self._poll_interval)
        while self._running:
            try:
                await self._poll_once()
            except Exception:
                logger.exception("Worker poll error")
            await asyncio.sleep(self._poll_interval)

    async def stop(self) -> None:
        self._running = False
        logger.info("Queue worker stopping")

    async def _poll_once(self) -> None:
        active_projects = await self._project_repo.list_by_status(ProjectStatus.ACTIVE)
        for project in active_projects:
            item = await self._queue_repo.get_oldest_pending(project.project_id, self._grace_period)
            if item is None:
                continue
            logger.info("Processing queue item %s for project %s", item.file_id, project.project_id)
            await self._process_service.execute(item.file_id, item.system_version)

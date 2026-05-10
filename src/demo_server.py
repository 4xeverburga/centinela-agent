import asyncio
import logging
import os
import sys
from functools import partial

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("centinela.demo")


def main() -> None:
    cfg = Config()
    loop = asyncio.new_event_loop()

    from ext.shared.db import get_connection
    from ext.repositories.sqlite_inspection_repository import SqliteInspectionRepository
    from ext.repositories.sqlite_history_repository import SqliteHistoryRepository
    from ext.repositories.sqlite_queue_repository import SqliteQueueRepository
    from ext.repositories.sqlite_project_repository import SqliteProjectRepository
    from ext.repositories.sqlite_human_review_repository import SqliteHumanReviewRepository
    from ext.providers.in_memory_image_gateway import InMemoryImageGateway
    from ext.providers.pillow_image_processor import PillowImageProcessor
    from ext.providers.system_clock import SystemClock
    from ext.providers.vllm_llm_inspector import VllmLLMInspector
    from app.domain.prompts import get_locale
    from app.services.process_queue_item import ProcessQueueItemService
    from ext.controllers.demo_api import create_demo_app

    image_gateway = InMemoryImageGateway()

    image_processor = PillowImageProcessor(
        max_long_edge=cfg.image_max_long_edge,
        jpeg_quality=cfg.image_jpeg_quality,
    )
    clock = SystemClock()
    locale = get_locale(cfg.bot_locale)
    llm_inspector = VllmLLMInspector(
        base_url=cfg.vllm_base_url,
        model=cfg.vllm_model,
        api_key="EMPTY",
        locale=cfg.bot_locale,
    )

    def _process_service_factory(queue_repo, project_repo, history_repo, inspection_repo, review_repo, telegram):
        return ProcessQueueItemService(
            queue_repo=queue_repo,
            project_repo=project_repo,
            history_repo=history_repo,
            inspection_repo=inspection_repo,
            review_repo=review_repo,
            telegram=telegram,
            image_processor=image_processor,
            llm_inspector=llm_inspector,
            clock=clock,
            locale=locale,
            system_version=cfg.system_version,
            context_max_messages=cfg.context_max_messages,
            context_window_before_minutes=cfg.context_window_before_minutes,
            context_window_after_minutes=cfg.context_window_after_minutes,
            max_attempts=cfg.worker_max_attempts,
            backoff_base=cfg.worker_backoff_base_seconds,
        )

    demo_db_path = os.path.splitext(cfg.sqlite_path)[0] + "_demo.db"

    demo_app = create_demo_app(
        api_key=cfg.demo_api_key,
        demo_sqlite_path=demo_db_path,
        db_connector=get_connection,
        inspection_repo_factory=SqliteInspectionRepository,
        history_repo_factory=SqliteHistoryRepository,
        queue_repo_factory=SqliteQueueRepository,
        project_repo_factory=SqliteProjectRepository,
        review_repo_factory=SqliteHumanReviewRepository,
        image_gateway=image_gateway,
        process_service_factory=_process_service_factory,
        system_version=cfg.system_version,
        loop=loop,
    )

    port = int(os.environ.get("DEMO_PORT", "5000"))
    logger.info("Starting demo API on port %d (db: %s)", port, demo_db_path)
    demo_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

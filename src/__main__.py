import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("centinela")


async def run() -> None:
    cfg = Config()
    logger.info("Config loaded: bot=%s model=%s", cfg.telegram_bot_display_name, cfg.vllm_model)

    from ext.shared.db import initialize_db
    conn = await initialize_db(cfg.sqlite_path)

    from ext.repositories.sqlite_project_repository import SqliteProjectRepository
    from ext.repositories.sqlite_user_repository import SqliteUserRepository
    from ext.repositories.sqlite_queue_repository import SqliteQueueRepository
    from ext.repositories.sqlite_history_repository import SqliteHistoryRepository
    from ext.repositories.sqlite_inspection_repository import SqliteInspectionRepository
    from ext.repositories.sqlite_human_review_repository import SqliteHumanReviewRepository

    project_repo = SqliteProjectRepository(conn)
    user_repo = SqliteUserRepository(conn)
    queue_repo = SqliteQueueRepository(conn)
    history_repo = SqliteHistoryRepository(conn)
    inspection_repo = SqliteInspectionRepository(conn)
    review_repo = SqliteHumanReviewRepository(conn)

    from ext.repositories.sqlite_admin_whitelist_repository import SqliteAdminWhitelistRepository
    admin_repo = SqliteAdminWhitelistRepository(conn)

    from ext.providers.system_clock import SystemClock, UuidIdGenerator
    clock = SystemClock()
    id_gen = UuidIdGenerator()

    admin_ids = [uid.strip() for uid in cfg.admin_telegram_user_ids.split(",") if uid.strip()]
    await admin_repo.seed(admin_ids, clock.now().isoformat())

    from ext.providers.pillow_image_processor import PillowImageProcessor
    image_processor = PillowImageProcessor(
        max_long_edge=cfg.image_max_long_edge,
        jpeg_quality=cfg.image_jpeg_quality,
    )

    from ext.providers.phash_image_embedder import PhashImageEmbedder
    image_embedder = PhashImageEmbedder(hash_size=8)

    from ext.providers.greedy_clustering_engine import GreedyClusteringEngine
    clustering_engine = GreedyClusteringEngine()

    from ext.providers.vllm_llm_inspector import VllmLLMInspector
    llm_inspector = VllmLLMInspector(
        base_url=cfg.vllm_base_url,
        model=cfg.vllm_model,
        api_key="EMPTY",
    )

    from ext.providers.vllm_report_generator import VllmReportGenerator
    report_gen = VllmReportGenerator(
        base_url=cfg.vllm_base_url,
        model=cfg.vllm_model,
        api_key="EMPTY",
    )

    import telegram
    from ext.providers.ptb_telegram_gateway import PtbTelegramGateway
    bot = telegram.Bot(token=cfg.bot_http_api_token)
    telegram_gw = PtbTelegramGateway(bot)

    from app.services.start_project import StartProjectService
    from app.services.finish_project import FinishProjectService
    from app.services.ingest_photo import IngestPhotoService
    from app.services.ingest_message import IngestMessageService
    from app.services.register_floorplan import RegisterFloorplanService
    from app.services.handle_hitl_response import HandleHITLResponseService
    from app.services.process_queue_item import ProcessQueueItemService

    start_svc = StartProjectService(project_repo, user_repo, telegram_gw, clock, id_gen)
    finish_svc = FinishProjectService(
        project_repo, inspection_repo, history_repo, review_repo, report_gen, telegram_gw, clock
    )
    ingest_photo_svc = IngestPhotoService(project_repo, queue_repo, clock)
    ingest_msg_svc = IngestMessageService(project_repo, history_repo, user_repo, clock)
    register_fp_svc = RegisterFloorplanService(project_repo, telegram_gw)
    hitl_svc = HandleHITLResponseService(review_repo, inspection_repo, clock)

    process_svc = ProcessQueueItemService(
        queue_repo=queue_repo,
        project_repo=project_repo,
        history_repo=history_repo,
        inspection_repo=inspection_repo,
        review_repo=review_repo,
        telegram=telegram_gw,
        image_processor=image_processor,
        image_embedder=image_embedder,
        clustering_engine=clustering_engine,
        llm_inspector=llm_inspector,
        clock=clock,
        sharpness_min=cfg.image_sharpness_min,
        similarity_threshold=cfg.image_similarity_threshold,
        context_max_messages=cfg.hitl_context_max_messages,
        context_window_minutes=cfg.hitl_context_window_minutes,
        max_attempts=cfg.worker_max_attempts,
        backoff_base=cfg.worker_backoff_base_seconds,
    )

    from ext.controllers.queue_worker import QueueWorker
    worker = QueueWorker(
        queue_repo=queue_repo,
        project_repo=project_repo,
        process_service=process_svc,
        poll_interval_seconds=cfg.worker_backoff_base_seconds,
    )

    from ext.controllers.telegram_bot import TelegramBotController
    from telegram.ext import ApplicationBuilder
    controller = TelegramBotController(
        start_svc, finish_svc, ingest_photo_svc, ingest_msg_svc, register_fp_svc, hitl_svc,
        admin_repo, telegram_gw,
    )

    app = ApplicationBuilder().token(cfg.bot_http_api_token).build()
    controller.register(app)

    worker_task = asyncio.create_task(worker.start())
    logger.info("Starting Telegram bot (long polling)...")

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()
    finally:
        await worker.stop()
        worker_task.cancel()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await conn.close()
        logger.info("Shutdown complete")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

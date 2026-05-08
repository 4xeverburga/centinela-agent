import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.services.start_project import StartProjectService
from app.services.finish_project import FinishProjectService
from app.services.ingest_photo import IngestPhotoService
from app.services.ingest_message import IngestMessageService
from app.services.register_floorplan import RegisterFloorplanService
from app.services.handle_hitl_response import HandleHITLResponseService

logger = logging.getLogger(__name__)


class TelegramBotController:
    def __init__(
        self,
        start_project_svc: StartProjectService,
        finish_project_svc: FinishProjectService,
        ingest_photo_svc: IngestPhotoService,
        ingest_message_svc: IngestMessageService,
        register_floorplan_svc: RegisterFloorplanService,
        hitl_svc: HandleHITLResponseService,
    ):
        self._start_project = start_project_svc
        self._finish_project = finish_project_svc
        self._ingest_photo = ingest_photo_svc
        self._ingest_message = ingest_message_svc
        self._register_floorplan = register_floorplan_svc
        self._hitl = hitl_svc

    def register(self, app: Application) -> None:
        app.add_handler(CommandHandler("iniciar", self._handle_start))
        app.add_handler(CommandHandler("finalizar", self._handle_finish))
        app.add_handler(CommandHandler("plano", self._handle_plano))
        app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        app.add_handler(CallbackQueryHandler(self._handle_callback, pattern=r"^hitl_"))

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return
        args = context.args or []
        local_name = " ".join(args) if args else "Sin nombre"
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        display = update.effective_user.full_name or user_id

        try:
            await self._start_project.execute(chat_id, local_name, user_id, display)
        except ValueError as e:
            await update.effective_message.reply_text(str(e))

    async def _handle_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None:
            return
        chat_id = str(update.effective_chat.id)
        try:
            await self._finish_project.execute(chat_id)
        except ValueError as e:
            await update.effective_message.reply_text(str(e))

    async def _handle_plano(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None:
            return
        msg = update.effective_message
        chat_id = str(update.effective_chat.id)

        if msg.document:
            file_id = msg.document.file_id
        elif msg.photo:
            file_id = msg.photo[-1].file_id
        elif msg.reply_to_message and msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message and msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            await msg.reply_text("Responda a una foto o envíe /plano con una imagen adjunta.")
            return

        ok = await self._register_floorplan.execute(chat_id, file_id)
        if not ok:
            await msg.reply_text("No hay proyecto activo en este grupo.")

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or not update.effective_message.photo:
            return
        chat_id = str(update.effective_chat.id)
        file_id = update.effective_message.photo[-1].file_id
        await self._ingest_photo.execute(chat_id, file_id)

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        display = update.effective_user.full_name or user_id
        text = update.effective_message.text or ""
        await self._ingest_message.execute(chat_id, user_id, display, text)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None:
            return
        await query.answer()

        data = query.data or ""
        parts = data.split("_")
        if len(parts) < 3:
            return

        action = parts[1]
        review_id = int(parts[2])
        reviewer_id = str(update.effective_user.id) if update.effective_user else ""

        answer = "confirmed" if action == "confirm" else "rejected"
        await self._hitl.execute(review_id, answer, reviewer_id)
        await query.edit_message_text(f"Revisión {review_id}: {answer}")

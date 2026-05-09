import logging

from telegram import ChatMember, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.ports.admin_whitelist_repository import AdminWhitelistRepository
from app.ports.telegram_gateway import TelegramGateway
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
        admin_repo: AdminWhitelistRepository,
        telegram_gw: TelegramGateway,
    ):
        self._start_project = start_project_svc
        self._finish_project = finish_project_svc
        self._ingest_photo = ingest_photo_svc
        self._ingest_message = ingest_message_svc
        self._register_floorplan = register_floorplan_svc
        self._hitl = hitl_svc
        self._admin_repo = admin_repo
        self._telegram = telegram_gw

    _ONBOARDING_TEXT = (
        "\U0001f477 *Hola, soy Centinela* \u2014 tu asistente de inspecci\u00f3n de obra.\n\n"
        "*Comandos disponibles:*\n"
        "`/iniciar <nombre>` \u2014 Abre un nuevo proyecto de inspecci\u00f3n.\n"
        "`/plano` \u2014 Registra el plano de referencia (responde a una foto).\n"
        "`/finalizar` \u2014 Cierra el proyecto activo y genera el reporte.\n\n"
        "Env\u00edame fotos de la obra y las registrar\u00e9 autom\u00e1ticamente. "
        "Si tengo dudas, te pedir\u00e9 confirmaci\u00f3n antes de registrar una observaci\u00f3n."
    )

    def _is_private(self, update: Update) -> bool:
        return update.effective_chat is not None and update.effective_chat.type == "private"

    def register(self, app: Application) -> None:
        app.add_handler(CommandHandler("start", self._handle_onboarding))
        app.add_handler(CommandHandler("iniciar", self._handle_start))
        app.add_handler(CommandHandler("finalizar", self._handle_finish))
        app.add_handler(CommandHandler("plano", self._handle_plano))
        app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        app.add_handler(CallbackQueryHandler(self._handle_callback, pattern=r"^hitl_"))
        app.add_handler(ChatMemberHandler(self._handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))

    async def _handle_onboarding(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None:
            return
        await update.effective_message.reply_text(self._ONBOARDING_TEXT, parse_mode="Markdown")

    async def _handle_bot_added(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        member = update.my_chat_member
        if member is None:
            return
        was_member = member.old_chat_member.status in (
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        )
        is_member = member.new_chat_member.status in (
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        )
        if not was_member and is_member:
            await context.bot.send_message(
                chat_id=member.chat.id,
                text=self._ONBOARDING_TEXT,
                parse_mode="Markdown",
            )

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        user_id = str(update.effective_user.id)

        if self._is_private(update):
            await update.effective_message.reply_text(
                "El comando /iniciar solo puede usarse en un grupo."
            )
            return

        if not await self._admin_repo.is_admin(user_id):
            await update.effective_message.reply_text(
                "Solo un administrador autorizado puede iniciar un proyecto."
            )
            return

        args = context.args or []
        local_name = " ".join(args) if args else "Sin nombre"
        chat_id = str(update.effective_chat.id)
        display = update.effective_user.full_name or user_id

        try:
            project = await self._start_project.execute(chat_id, local_name, user_id, display)
        except ValueError as e:
            await update.effective_message.reply_text(str(e))
            return

        try:
            await self._telegram.send_message(
                user_id,
                "\U0001f4cb Proyecto iniciado: " + local_name + "\n"
                "ID: " + project.project_id + "\n\n"
                "Env\u00edame el plano del local como foto o documento en este chat privado "
                "y lo registrar\u00e9 autom\u00e1ticamente.\n\n"
                "Tambi\u00e9n puedes enviarme instrucciones especiales para este proyecto.",
            )
        except Exception:
            logger.warning(
                "Could not DM admin %s -- they need to /start the bot first", user_id
            )
            await update.effective_message.reply_text(
                "\u26a0\ufe0f No pude enviarte un mensaje privado. "
                "Aseg\u00farate de iniciar el bot con /start antes de usar /iniciar."
            )

    async def _handle_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        user_id = str(update.effective_user.id)
        if not await self._admin_repo.is_admin(user_id):
            await update.effective_message.reply_text(
                "Solo un administrador autorizado puede finalizar un proyecto."
            )
            return

        chat_id = str(update.effective_chat.id)
        try:
            await self._finish_project.execute(chat_id)
        except ValueError as e:
            await update.effective_message.reply_text(str(e))

    async def _handle_plano(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        user_id = str(update.effective_user.id)
        if not await self._admin_repo.is_admin(user_id):
            await update.effective_message.reply_text(
                "Solo un administrador puede registrar el plano."
            )
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
            await msg.reply_text("Responda a una foto o env\u00ede /plano con una imagen adjunta.")
            return

        ok = await self._register_floorplan.execute(chat_id, file_id)
        if not ok:
            await msg.reply_text("No hay proyecto activo en este grupo.")

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or not update.effective_message.photo:
            return

        if self._is_private(update):
            if update.effective_user is None:
                return
            user_id = str(update.effective_user.id)
            if not await self._admin_repo.is_admin(user_id):
                return
            return

        chat_id = str(update.effective_chat.id)
        file_id = update.effective_message.photo[-1].file_id
        await self._ingest_photo.execute(chat_id, file_id)

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        if self._is_private(update):
            user_id = str(update.effective_user.id)
            if not await self._admin_repo.is_admin(user_id):
                return
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
        await query.edit_message_text("Revisi\u00f3n " + str(review_id) + ": " + answer)

import logging
from types import ModuleType

from telegram import ChatMember, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.domain.entities import IngestResult, ReviewTrigger
from app.ports.admin_whitelist_repository import AdminWhitelistRepository
from app.ports.assistant_repository import AssistantRepository
from app.ports.inspection_repository import InspectionRepository
from app.ports.human_review_repository import HumanReviewRepository
from app.ports.project_repository import ProjectRepository
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
        assistant_repo: AssistantRepository,
        project_repo: ProjectRepository,
        inspection_repo: InspectionRepository,
        review_repo: HumanReviewRepository,
        telegram_gw: TelegramGateway,
        locale: ModuleType,
    ):
        self._start_project = start_project_svc
        self._finish_project = finish_project_svc
        self._ingest_photo = ingest_photo_svc
        self._ingest_message = ingest_message_svc
        self._register_floorplan = register_floorplan_svc
        self._hitl = hitl_svc
        self._admin_repo = admin_repo
        self._assistant_repo = assistant_repo
        self._project_repo = project_repo
        self._inspection_repo = inspection_repo
        self._review_repo = review_repo
        self._telegram = telegram_gw
        self._locale = locale

    def _is_private(self, update: Update) -> bool:
        return update.effective_chat is not None and update.effective_chat.type == "private"

    async def _is_admin_or_assistant(self, user_id: str) -> bool:
        return await self._admin_repo.is_admin(user_id) or await self._assistant_repo.is_assistant(user_id)

    def register(self, app: Application) -> None:
        app.add_handler(CommandHandler("start", self._handle_onboarding))
        app.add_handler(CommandHandler("hola", self._handle_onboarding))
        app.add_handler(CommandHandler("iniciar", self._handle_start))
        app.add_handler(CommandHandler("finalizar", self._handle_finish))
        app.add_handler(CommandHandler("plano", self._handle_plano))
        app.add_handler(CommandHandler("alertas", self._handle_alertas))
        app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        app.add_handler(CallbackQueryHandler(self._handle_callback, pattern=r"^hitl_"))
        app.add_handler(ChatMemberHandler(self._handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))

    async def _handle_onboarding(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None:
            return
        await update.effective_message.reply_text(self._locale.ONBOARDING, parse_mode="Markdown")

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
                text=self._locale.ONBOARDING,
                parse_mode="Markdown",
            )

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        user_id = str(update.effective_user.id)

        if self._is_private(update):
            await update.effective_message.reply_text(self._locale.START_GROUP_ONLY)
            return

        if not await self._admin_repo.is_admin(user_id):
            await update.effective_message.reply_text(self._locale.START_ADMIN_ONLY)
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
                self._locale.START_DM_TEXT.format(name=local_name, project_id=project.project_id),
            )
        except Exception:
            logger.warning(
                "Could not DM admin %s -- they need to /start the bot first", user_id
            )
            await update.effective_message.reply_text(self._locale.START_DM_FAILED)

    async def _handle_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        user_id = str(update.effective_user.id)
        if not await self._admin_repo.is_admin(user_id):
            await update.effective_message.reply_text(self._locale.FINISH_ADMIN_ONLY)
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
            await update.effective_message.reply_text(self._locale.PLANO_ADMIN_ONLY)
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
            await msg.reply_text(self._locale.PLANO_NO_IMAGE)
            return

        ok = await self._register_floorplan.execute(chat_id, file_id)
        if not ok:
            await msg.reply_text(self._locale.PLANO_NO_PROJECT)

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
        user_id = str(update.effective_user.id) if update.effective_user else ""
        display = update.effective_user.full_name if update.effective_user else ""
        file_id = update.effective_message.photo[-1].file_id
        caption = update.effective_message.caption or ""
        cluster_id = update.effective_message.media_group_id or ""
        msg_id = update.effective_message.message_id
        result = await self._ingest_photo.execute(chat_id, file_id, user_id, display, caption, cluster_id, msg_id)
        if result == IngestResult.REJECTED_BLURRY:
            await self._telegram.send_message(chat_id, self._locale.BLURRY_IMAGE)

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
        msg_id = update.effective_message.message_id
        await self._ingest_message.execute(chat_id, user_id, display, text, msg_id)

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
        reviewer_name = update.effective_user.full_name if update.effective_user else reviewer_id

        answer = "confirmed" if action == "confirm" else "rejected"
        await self._hitl.execute(review_id, answer, reviewer_id)
        try:
            if answer == "confirmed":
                msg = self._locale.HITL_CONFIRMED.format(review_id=review_id, reviewer=reviewer_name)
            else:
                msg = self._locale.HITL_REJECTED.format(review_id=review_id, reviewer=reviewer_name)
            await query.edit_message_text(msg, parse_mode="Markdown")
        except BadRequest as e:
            if "not modified" in str(e).lower():
                pass
            else:
                raise

    async def _handle_alertas(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        user_id = str(update.effective_user.id)
        is_admin = await self._admin_repo.is_admin(user_id)
        is_assistant = await self._assistant_repo.is_assistant(user_id)

        if not is_admin and not is_assistant:
            await update.effective_message.reply_text(self._locale.ALERTS_UNAUTHORIZED)
            return

        chat_id = str(update.effective_chat.id)
        from app.domain.entities import ProjectStatus
        project = await self._project_repo.get_active_by_chat(chat_id)
        if project is None:
            await update.effective_message.reply_text(self._locale.ALERTS_NO_PROJECT)
            return

        if is_assistant and not is_admin:
            admin_ids = await self._assistant_repo.get_admin_ids_for_assistant(user_id)
            if project.admin_user_id not in admin_ids:
                await update.effective_message.reply_text(self._locale.ALERTS_UNAUTHORIZED)
                return

        alerts = await self._review_repo.get_pending_for_project(project.project_id)
        suspicious = [r for r in alerts if r.trigger == ReviewTrigger.SUSPICIOUS_CATEGORY][:5]
        if not suspicious:
            await update.effective_message.reply_text(self._locale.ALERTS_EMPTY)
            return

        total = len(suspicious)
        await update.effective_message.reply_text(
            self._locale.ALERTS_HEADER.format(count=total), parse_mode="Markdown"
        )

        for idx, review in enumerate(suspicious, 1):
            inspection = await self._inspection_repo.get_by_image_file_id(review.image_file_id)
            if inspection is None:
                continue
            caption = self._locale.ALERT_CAPTION.format(
                idx=idx,
                category=inspection.category,
                reason=inspection.ai_system_observation or "-",
                location=inspection.location_on_map or "-",
            )
            await self._telegram.send_photo(
                chat_id, inspection.image_file_id, caption
            )
            await self._telegram.send_inline_keyboard(
                chat_id,
                self._locale.HITL_QUESTION,
                [[
                    {"text": self._locale.HITL_CONFIRM_BUTTON, "callback_data": f"hitl_confirm_{review.id}"},
                    {"text": self._locale.HITL_REJECT_BUTTON, "callback_data": f"hitl_reject_{review.id}"},
                ]],
            )

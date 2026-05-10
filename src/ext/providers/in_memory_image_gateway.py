import logging

from app.ports.telegram_gateway import TelegramGateway

logger = logging.getLogger(__name__)


class InMemoryImageGateway(TelegramGateway):
    def __init__(self):
        self._store: dict[str, bytes] = {}

    def put(self, file_id: str, data: bytes) -> None:
        self._store[file_id] = data

    async def download_file(self, file_id: str) -> bytes:
        if file_id not in self._store:
            raise KeyError(f"file_id {file_id!r} not found in demo image store")
        return self._store[file_id]

    async def send_message(self, chat_id: str, text: str) -> None:
        logger.debug("demo send_message chat_id=%s text=%s", chat_id, text[:80])

    async def send_inline_keyboard(
        self, chat_id: str, text: str, buttons: list[list[dict[str, str]]]
    ) -> int:
        logger.debug("demo send_inline_keyboard chat_id=%s", chat_id)
        return 0

    async def edit_message(self, chat_id: str, message_id: int, text: str) -> None:
        logger.debug("demo edit_message chat_id=%s message_id=%d", chat_id, message_id)

    async def send_document(self, chat_id: str, file_bytes: bytes, filename: str) -> None:
        logger.debug("demo send_document chat_id=%s filename=%s", chat_id, filename)

    async def send_photo(self, chat_id: str, file_id: str, caption: str) -> None:
        logger.debug("demo send_photo chat_id=%s file_id=%s", chat_id, file_id)

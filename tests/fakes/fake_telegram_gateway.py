from app.ports.telegram_gateway import TelegramGateway


class FakeTelegramGateway(TelegramGateway):
    def __init__(self):
        self.sent_messages: list[tuple[str, str]] = []
        self.sent_documents: list[tuple[str, bytes, str]] = []
        self.sent_keyboards: list[tuple[str, str, list]] = []
        self.edited_messages: list[tuple[str, int, str]] = []
        self._files: dict[str, bytes] = {}

    def set_file(self, file_id: str, data: bytes) -> None:
        self._files[file_id] = data

    async def download_file(self, file_id: str) -> bytes:
        return self._files.get(file_id, b"")

    async def send_message(self, chat_id: str, text: str) -> None:
        self.sent_messages.append((chat_id, text))

    async def send_inline_keyboard(
        self, chat_id: str, text: str, buttons: list[list[dict[str, str]]]
    ) -> int:
        self.sent_keyboards.append((chat_id, text, buttons))
        return len(self.sent_keyboards)

    async def edit_message(self, chat_id: str, message_id: int, text: str) -> None:
        self.edited_messages.append((chat_id, message_id, text))

    async def send_document(self, chat_id: str, file_bytes: bytes, filename: str) -> None:
        self.sent_documents.append((chat_id, file_bytes, filename))

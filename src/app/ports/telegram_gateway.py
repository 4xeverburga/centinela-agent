from abc import ABC, abstractmethod


class TelegramGateway(ABC):
    @abstractmethod
    async def download_file(self, file_id: str) -> bytes: ...

    @abstractmethod
    async def send_message(self, chat_id: str, text: str) -> None: ...

    @abstractmethod
    async def send_inline_keyboard(
        self, chat_id: str, text: str, buttons: list[list[dict[str, str]]]
    ) -> int: ...

    @abstractmethod
    async def edit_message(self, chat_id: str, message_id: int, text: str) -> None: ...

    @abstractmethod
    async def send_document(self, chat_id: str, file_bytes: bytes, filename: str) -> None: ...

    @abstractmethod
    async def send_photo(self, chat_id: str, file_id: str, caption: str) -> None: ...

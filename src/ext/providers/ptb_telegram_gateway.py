import telegram

from app.ports.telegram_gateway import TelegramGateway


class PtbTelegramGateway(TelegramGateway):
    def __init__(self, bot: telegram.Bot):
        self._bot = bot

    async def download_file(self, file_id: str) -> bytes:
        f = await self._bot.get_file(file_id)
        ba = await f.download_as_bytearray()
        return bytes(ba)

    async def send_message(self, chat_id: str, text: str) -> None:
        await self._bot.send_message(chat_id=int(chat_id), text=text)

    async def send_inline_keyboard(
        self, chat_id: str, text: str, buttons: list[list[dict[str, str]]]
    ) -> int:
        keyboard = []
        for row in buttons:
            keyboard.append([
                telegram.InlineKeyboardButton(text=b["text"], callback_data=b["callback_data"])
                for b in row
            ])
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        msg = await self._bot.send_message(
            chat_id=int(chat_id), text=text, reply_markup=reply_markup
        )
        return msg.message_id

    async def edit_message(self, chat_id: str, message_id: int, text: str) -> None:
        await self._bot.edit_message_text(
            chat_id=int(chat_id), message_id=message_id, text=text
        )

    async def send_document(self, chat_id: str, file_bytes: bytes, filename: str) -> None:
        from io import BytesIO
        doc = BytesIO(file_bytes)
        doc.name = filename
        await self._bot.send_document(chat_id=int(chat_id), document=doc)

    async def send_photo(self, chat_id: str, file_id: str, caption: str) -> None:
        await self._bot.send_photo(chat_id=int(chat_id), photo=file_id, caption=caption)

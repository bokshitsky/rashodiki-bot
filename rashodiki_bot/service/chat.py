from datetime import datetime

from rashodiki_bot.db import with_session, get_current_session, transactional
from rashodiki_bot.model import Chat


class ChatService:
    @with_session
    async def get_chat(self, chat_id: int) -> Chat:
        return await get_current_session().get(Chat, chat_id)

    @transactional
    async def set_workbook_url(self, chat_id: int, workbook_url: str):
        chat = await self.get_chat(chat_id)
        chat.workbook_url = workbook_url
        get_current_session().add(chat)

    @transactional
    async def set_default_currency(self, chat_id: int, default_currency: str):
        chat = await self.get_chat(chat_id)
        chat.default_currency = default_currency
        get_current_session().add(chat)

    @transactional
    async def set_default_worksheet(self, chat_id: int, worksheet_name: str):
        chat = await self.get_chat(chat_id)
        chat.worksheet_name = worksheet_name
        get_current_session().add(chat)

    @transactional
    async def add_chat(self, chat_id: int):
        chat = Chat(chat_id=chat_id, creation_time=datetime.now(), workbook_url=None)
        get_current_session().add(chat)
        await get_current_session().flush()
        return chat

from datetime import datetime

import gspread_asyncio
from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager, AsyncioGspreadClient

from rashodiki_bot.db import with_session, get_current_session, transactional
from rashodiki_bot.model import Chat
from rashodiki_bot.parser import SpendInfo
from rashodiki_bot.settings import settings

DEFAULT_WORKSHEET = "rashodiki"


def get_creds() -> Credentials:
    return Credentials.from_service_account_file(settings().google_service_account_file).with_scopes(
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )


def get_client_manager():
    return gspread_asyncio.AsyncioGspreadClientManager(get_creds)


class WbService:
    def __init__(self, agcm: AsyncioGspreadClientManager):
        self.agcm = agcm
        self.agc: AsyncioGspreadClient | None = None

    async def save_spend(self, chat: Chat, date: datetime, username, row: SpendInfo):
        await self.try_authorize()
        worksheet = await self._get_worksheet(chat)
        row = [str(date), username, row.amount, row.currency or chat.default_currency, row.description]
        await worksheet.insert_row(row, index=2)

    async def remove_last(self, chat: Chat) -> SpendInfo | None:
        await self.try_authorize()
        worksheet = await self._get_worksheet(chat)
        values = await worksheet.get_values("A2:E2")
        if not values:
            return None
        row = values[0]
        await worksheet.delete_row(index=2)
        return SpendInfo(amount=int(row[2]), currency=row[3], description=row[4])

    async def _get_worksheet(self, chat: Chat):
        wb = await self.agc.open_by_url(chat.workbook_url)
        sheet = chat.worksheet_name or DEFAULT_WORKSHEET
        return await wb.worksheet(sheet)

    async def try_authorize(self):
        agc = await self.agcm.authorize()
        if agc != self.agc:
            self.agc = agc
        return self.agc


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
        chat = Chat(chat_id=chat_id, creation_time=datetime.now())
        get_current_session().add(chat)
        await get_current_session().flush()
        return chat

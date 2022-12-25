from datetime import datetime

import gspread_asyncio
from google.oauth2.service_account import Credentials
from gspread import WorksheetNotFound
from gspread.exceptions import APIError
from gspread_asyncio import AsyncioGspreadClientManager, AsyncioGspreadClient

from rashodiki_bot.model import Chat, TransferInfo, ResponseException
from rashodiki_bot.settings import settings


class WorkbookError(RuntimeError):
    def __init__(self):
        pass


class WbService:
    def __init__(self, agcm: AsyncioGspreadClientManager):
        self.agcm = agcm
        self.agc: AsyncioGspreadClient | None = None

    async def save_spend(self, chat: Chat, date: datetime, username, row: TransferInfo):
        await self.try_authorize()
        worksheet = await self.get_worksheet(chat)
        row = [str(date), username, row.amount, row.currency, row.description]
        await worksheet.insert_row(row, index=2)

    async def remove_last(self, chat: Chat) -> TransferInfo | None:
        await self.try_authorize()
        worksheet = await self.get_worksheet(chat)
        values = await worksheet.get_values("A2:E2")
        if not values:
            return None
        row = values[0]
        await worksheet.delete_row(index=2)
        return TransferInfo(amount=int(row[2]), currency=row[3], description=row[4])

    async def get_worksheet(self, chat: Chat):
        wb = await self.get_workbook(chat.workbook_url)
        sheet = chat.get_worksheet_name()
        try:
            return await wb.worksheet(sheet)
        except WorksheetNotFound:
            return await wb.add_worksheet(sheet, rows=500, cols=15)

    async def get_workbook(self, workbook_url: str):
        await self.try_authorize()
        try:
            return await self.agc.open_by_url(workbook_url)
        except APIError:
            raise ResponseException(
                "Ошибка при обращении к воркбуку, проверь его настройки доступа и "
                "правильную ли ссылку сохранил через /settings"
            )

    async def try_authorize(self):
        agc = await self.agcm.authorize()
        if agc != self.agc:
            self.agc = agc
        return self.agc


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

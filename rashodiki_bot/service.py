import gspread_asyncio
from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager, AsyncioGspreadClient

from rashodiki_bot.model import Session
from rashodiki_bot.parser import RashodikInfo
from rashodiki_bot.settings import settings


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


class RashodikiService:
    def __init__(self, agcm: AsyncioGspreadClientManager):
        self.agcm = agcm
        self.agc: AsyncioGspreadClient | None = None

    async def save_rashodik(self, date, username, rashodik: RashodikInfo):
        await self.try_authorize()
        wb = await self.agc.open_by_url(settings().wb_url)
        worksheet = await wb.worksheet("rashodiki")

        rashodik = [str(date), username, rashodik.amount, rashodik.currency, rashodik.description]
        await worksheet.insert_row(rashodik, index=2)

    async def remove_last(self) -> RashodikInfo | None:
        await self.try_authorize()
        wb = await self.agc.open_by_url(settings().wb_url)
        worksheet = await wb.worksheet("rashodiki")
        values = await worksheet.get_values("A2:E2")
        if not values:
            return None
        row = values[0]
        await worksheet.delete_row(index=2)
        return RashodikInfo(amount=int(row[2]), currency=row[3], description=row[4])

    async def try_authorize(self):
        agc = await self.agcm.authorize()
        if agc != self.agc:
            self.agc = agc
        return self.agc

class UserService:

    async def test(self):
        Session()

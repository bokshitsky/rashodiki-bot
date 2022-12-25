from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from rashodiki_bot.model import ResponseException
from rashodiki_bot.service.chat import ChatService
from rashodiki_bot.service.workbook import WbService, get_client_manager
from rashodiki_bot.settings import settings

bot = Bot(settings().tg_token)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)
wb_service = WbService(get_client_manager())
chat_service = ChatService()


async def get_chat(message):
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        ResponseException("Ты не зарегистрирован в системе, сделай /start")
    return chat


async def validate_has_workbook(chat):
    if not chat.workbook_url:
        raise ResponseException("Сначала нужно задать workbook, куда сохранять данные через /settings")

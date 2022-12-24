import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, BotCommand
from aiogram.utils import executor

from rashodiki_bot.model import Session
from rashodiki_bot.parser import parse_rashodik, ParseError, ParseErrorType
from rashodiki_bot.service import get_client_manager, RashodikiService
from rashodiki_bot.settings import settings, init_settings

init_settings(os.environ.get("RASHODIKI_ENV_FILE", "../config.env"))

bot = Bot(
    settings().tg_token,
)

dispatcher = Dispatcher(bot)
service = RashodikiService(get_client_manager())


@dispatcher.message_handler(commands=["start"])
async def register_and_send_welcome(message: types.Message):
    await message.answer(
        text=f"Привет, я расходики-бот. Шли мне расходы-доходы и я их запишу.",
        parse_mode=ParseMode.MARKDOWN,
    )


@dispatcher.message_handler(commands=["remove_last"])
async def remove_last(message: types.Message):
    await message.answer(text="Пробую найти, что удалить...")
    removed = await service.remove_last()
    if not removed:
        return await message.answer(text="Не нашел, что удалить")
    await message.answer(text=f"Удалил: {removed.amount} {removed.currency} {removed.description}")


@dispatcher.message_handler()
async def send_any(message: types.Message):
    await message.answer(text="Пробую понять, что тут...")
    try:
        parsed = parse_rashodik(message.text)
    except ParseError as ex:
        match ex.error:
            case ParseErrorType.NO_AMOUNT:
                return await message.answer(text="Не понял, какая сумма")
            case ParseErrorType.NO_CURRENCY:
                return await message.answer(text="Не понял, какая валюта")
            case ParseErrorType.NO_CURRENCY:
                return await message.answer(text="Не понял, на что")
            case _:
                raise ex from None

    await service.save_rashodik(message.date, message.chat.username, parsed)
    response = f"Записал: {parsed.amount} {parsed.currency} {parsed.description}"
    await message.answer(text=response)


def main():
    async def _set_commands(disp):
        await disp.bot.set_my_commands(
            commands=[
                BotCommand(
                    command="/start",
                    description="Начать работу",
                ),
                BotCommand(
                    command="/remove_last",
                    description="Удалить последнюю записанную трату",
                ),
                BotCommand(
                    command="/set_default_currency",
                    description="Установить дефолтную валюту",
                ),
                BotCommand(
                    command="/set_workbook",
                    description="Установить, куда слать данные. Если не задано, то шлю в налоговую",
                ),
                BotCommand(
                    command="/help",
                    description="Пояснить, как я работаю",
                ),
            ]
        )

    executor.start_polling(dispatcher, skip_updates=True, on_startup=_set_commands)


async def test():
    async with Session() as ses:
        


if __name__ == "__main__":
    asyncio.run(test())

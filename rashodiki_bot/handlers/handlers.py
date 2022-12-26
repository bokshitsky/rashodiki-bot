from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ParseMode

from rashodiki_bot.handlers import dispatcher, chat_service
from rashodiki_bot.model import ResponseException


@dispatcher.errors_handler(exception=ResponseException)
async def response_error_handler(update, exception: ResponseException):
    if exception.reply:
        await update.message.reply(exception.text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.answer(exception.text, parse_mode=ParseMode.MARKDOWN)
    return False


@dispatcher.message_handler(Command("start"), state="*")
async def handle_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(f"Привет я Гешефт-Боткш, записываю расходы-доходы в гугл-таблицу")
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        chat = await chat_service.add_chat(message.chat.id)
        await message.answer("Зарегал тебя в системе")

    if chat.workbook_url is None:
        await message.answer("Теперь нужно привязать гугловую таблицу, куда я буду сохранять данные.")
        await message.answer("Нажми /settings и выбери `Workbook`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("Можешь вводить /spending или /income, либо просто написать сюда сколько потратил")

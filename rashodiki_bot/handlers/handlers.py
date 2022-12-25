from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ParseMode

from rashodiki_bot.handlers import dispatcher, chat_service
from rashodiki_bot.model import ResponseException


@dispatcher.errors_handler(exception=ResponseException)
async def response_error_handler(update, exception: ResponseException):
    if exception.reply:
        await update.message.reply(exception.text)
    else:
        await update.message.answer(exception.text)
    return False


@dispatcher.message_handler(Command("start"), state="*")
async def handle_start(message: types.Message, state: FSMContext):
    await state.finish()
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        chat = await chat_service.add_chat(message.chat.id)
        await message.answer("Зарегал тебя в системе")

    if chat.workbook_url is None:
        await message.answer("Теперь нужно привязать гугловый ворбук, куда я буду сохранять данные.")
        await message.answer("Нажми /settings и выбери `Workbook`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("Теперь можешь вводить /spending или /income, либо просто написать сюда сколько потратил")

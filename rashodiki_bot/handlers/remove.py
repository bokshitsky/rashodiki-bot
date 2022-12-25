from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from rashodiki_bot.handlers import wb_service, dispatcher, get_chat, validate_has_workbook


@dispatcher.message_handler(Command("remove"), state="*")
async def remove_last(message: types.Message, state: FSMContext):
    await state.finish()
    chat = await get_chat(message)
    await validate_has_workbook(chat)
    msg = await message.answer(text="Удаляю...")

    removed = await wb_service.remove_last(chat)
    if not removed:
        return await message.edit_text(text="Не нашел, что удалить")
    await msg.edit_text(text=f"Удалил: {abs(removed.amount)} {removed.currency} {removed.description}")

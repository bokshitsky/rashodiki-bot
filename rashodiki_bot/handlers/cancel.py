from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from rashodiki_bot.handlers import dispatcher


@dispatcher.message_handler(commands="cancel", state="*")
@dispatcher.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.answer("Отменяю", reply_markup=types.ReplyKeyboardRemove())

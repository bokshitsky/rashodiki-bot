from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ParseMode

from rashodiki_bot.handlers import dispatcher, get_chat, chat_service, wb_service
from rashodiki_bot.settings import bot_google_email


class Settings(StatesGroup):
    select_setting = State()

    set_workbook = State()
    set_worksheet = State()


@dispatcher.message_handler(Command("settings"), state="*")
async def select_settings_action(message: types.Message, state: FSMContext):
    await state.finish()
    chat = await get_chat(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, row_width=2)
    markup.add("Workbook", "Worksheet", "Показать текущие настройки")
    await Settings.select_setting.set()
    await message.answer("Что хочешь настроить?", reply_markup=markup)


@dispatcher.message_handler(state=Settings.select_setting, text="Workbook")
async def choose_workbook(message: types.Message, state: FSMContext):
    await message.answer(
        f"Пришли ссылку на workbook.\n"
        f'Ссылка выглядит: `https://docs.google.com/spreadsheets...`"\n\n'
        f"Он должен быть доступен на редактирование юзеру `{bot_google_email}`\n(либо доступен всем на редактирование "
        f"по ссылке)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=types.ReplyKeyboardRemove()
    )
    await Settings.set_workbook.set()


@dispatcher.message_handler(state=Settings.set_workbook, regexp=".*docs.google.com/spreadsheets.*")
async def set_workbook(message: types.Message, state: FSMContext):
    chat = await get_chat(message)
    url = message.text.strip()
    await wb_service.get_workbook(url)
    await chat_service.set_workbook_url(chat.chat_id, url)
    await state.finish()
    await message.reply("Сохранил")


@dispatcher.message_handler(state=Settings.set_workbook)
async def set_workbook(message: types.Message, state: FSMContext):
    await message.reply('Это не ссылка на workbook, ссылка должна содержать "https://docs.google.com/spreadsheets..."')


@dispatcher.message_handler(state=Settings.select_setting, text="Worksheet")
async def choose_worksheet(message: types.Message, state: FSMContext):
    chat = await get_chat(message)
    await message.answer(
        f"Пришли название листа, в который нужно сохранять данные\n"
        f"(сейчас использую `{chat.get_worksheet_name()}`)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await Settings.set_worksheet.set()


@dispatcher.message_handler(state=Settings.set_worksheet)
async def set_worksheet(message: types.Message, state: FSMContext):
    chat = await get_chat(message)
    worksheet_name = message.text.strip()
    await chat_service.set_default_worksheet(chat.chat_id, worksheet_name)
    await state.finish()
    await message.reply(
        f"Сохранил название `{worksheet_name}`", parse_mode=ParseMode.MARKDOWN, reply_markup=types.ReplyKeyboardRemove()
    )


@dispatcher.message_handler(state=Settings.select_setting, text="Показать текущие настройки")
async def show_current(message: types.Message, state: FSMContext):
    chat = await get_chat(message)
    await state.finish()
    await message.answer(f"workbook: {chat.workbook_url or 'НЕ ЗАДАН'}")
    await message.answer(f"worksheet: `{chat.get_worksheet_name()}`", reply_markup=types.ReplyKeyboardRemove())

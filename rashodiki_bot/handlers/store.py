from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State

from rashodiki_bot.handlers import dispatcher, wb_service, get_chat, validate_has_workbook
from rashodiki_bot.model import CURRENCY_LIST, TransferInfo


class MoneyTransfer(StatesGroup):
    select_amount = State()
    select_currency = State()
    select_description = State()


@dispatcher.message_handler(Command("spending"), state="*")
async def start_spending_save(message: types.Message, state: FSMContext):
    await state.finish()
    chat = await get_chat(message)
    await validate_has_workbook(chat)
    await message.answer("Cколько потратил?", reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(sign=-1)
    await MoneyTransfer.select_amount.set()


@dispatcher.message_handler(Command("income"), state="*")
async def start_income_save(message: types.Message, state: FSMContext):
    await state.finish()
    chat = await get_chat(message)
    await validate_has_workbook(chat)
    await message.answer("Cколько заработал?", reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(sign=1)
    await MoneyTransfer.select_amount.set()


@dispatcher.message_handler(filters.Regexp("([-+]?[0-9]+)"))
@dispatcher.message_handler(state=MoneyTransfer.select_amount)
async def amount_chosen(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        sign = data.get("sign")
        if sign is None:
            sign = 1 if message.text.startswith("+") else -1

        data["amount"] = sign * abs(int(message.text.strip()))

    await MoneyTransfer.select_currency.set()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, row_width=4)
    markup.add(*CURRENCY_LIST)
    markup.add("/cancel")

    await message.reply("Выбери валюту:", reply_markup=markup)


@dispatcher.message_handler(state=MoneyTransfer.select_currency)
async def currency_chosen(message: types.Message, state: FSMContext):
    await state.update_data(currency=message.text.strip())
    # chat = await get_chat(message)
    await MoneyTransfer.select_description.set()
    # last_values = await wb_service.get_last_description(chat)

    # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, row_width=4)
    # markup.add(*last_values)

    data = await state.get_data()
    msg = "Источник дохода?" if data["amount"] > 0 else "На что потратил?"
    await message.reply(f"{msg}")


@dispatcher.message_handler(state=MoneyTransfer.select_description)
async def description_chosen(message: types.Message, state: FSMContext):
    chat = await get_chat(message)
    description = message.text.strip()

    data = await state.get_data()
    transfer_info = TransferInfo(amount=data["amount"], currency=data["currency"], description=description)

    shown_amount = abs(transfer_info.amount)

    text = f"Записываю: {shown_amount} {transfer_info.currency} {transfer_info.description}..."
    msg = await message.reply(text=text)
    await state.finish()
    await wb_service.save_spend(chat, message.date, message.chat.username, transfer_info)
    await msg.edit_text(f"Записал: {shown_amount} {transfer_info.currency} {transfer_info.description}")

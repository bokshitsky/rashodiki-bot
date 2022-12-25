from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, BotCommand
from aiogram.utils import executor

from rashodiki_bot.model import run_alembic_migration
from rashodiki_bot.parser import parse_rashodik, ParseError, ParseErrorType
from rashodiki_bot.service import get_client_manager, WbService, ChatService, DEFAULT_WORKSHEET
from rashodiki_bot.settings import settings, bot_google_email

bot = Bot(settings().tg_token)

dispatcher = Dispatcher(bot)
wb_service = WbService(get_client_manager())
chat_service = ChatService()


@dispatcher.message_handler(commands=["help"])
async def handle_help(message: types.Message):
    await message.answer(get_description_message(), parse_mode=ParseMode.MARKDOWN)


def get_description_message():
    return (
        f"Присылай мне свои расходы:\n"
        "`10000 на хлеб`\n"
        "`10000др продукты`\n"
        "`10000рублей потратил на такси`\n"
        "`10000руб пакет в магазине`\n\n"
        "Или доходы:\n"
        "`+15 за пост`\n\n"
        "Чтобы я знал, куда сохранить пришли мне ссылку на google workbook вида:\n"
        "`https://docs.google.com/spreadsheets/d...`\n"
        "Этот WB должен быть доступен на редактирование по ссылке, либо доступен для пользователя\n"
        f"{bot_google_email}\n\n"
        "Если хочешь задать дефолтную валюту пришли:\n"
        "`валюта монетки`\n\n"
        f"Если хочешь задать worksheet (отличный от `{DEFAULT_WORKSHEET}`) пришли:\n"
        "`sheet sheet_name`\n\n"
    )


@dispatcher.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await message.answer(
        text=f"Привет, я бот для записи расходов. Шли мне расходы-доходы и я их запишу.",
        parse_mode=ParseMode.MARKDOWN,
    )
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        await chat_service.add_chat(message.chat.id)
        await message.answer("Зарегал тебя в системе", parse_mode=ParseMode.MARKDOWN)
        return await message.answer(get_description_message(), parse_mode=ParseMode.MARKDOWN)


@dispatcher.message_handler(commands=["remove"])
async def remove_last(message: types.Message):
    await message.answer(text="Пробую найти, что удалить...")
    chat = await chat_service.get_chat(message.chat.id)
    removed = await wb_service.remove_last(chat)
    if not removed:
        return await message.answer(text="Не нашел, что удалить")
    await message.answer(text=f"Удалил: {removed.amount} {removed.currency} {removed.description}")


@dispatcher.message_handler(regexp="docs.google.com/spreadsheets")
async def save_workbook_for_current_user(message: types.Message):
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Тебя нет в системе, сначала набери `/start`", parse_mode=ParseMode.MARKDOWN)
    await chat_service.set_workbook_url(chat.chat_id, message.text.strip())
    return await message.answer("Привязал workbook", parse_mode=ParseMode.MARKDOWN)


@dispatcher.message_handler(regexp="^валюта .*")
async def save_default_currency_for_current_user(message: types.Message):
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Тебя нет в системе, сначала набери `/start`", parse_mode=ParseMode.MARKDOWN)
    default_currency = message.text.removeprefix("валюта").strip()
    await chat_service.set_default_currency(chat.chat_id, default_currency)
    return await message.answer(f"Привязал дефолтную валюту `{default_currency}`", parse_mode=ParseMode.MARKDOWN)


@dispatcher.message_handler(regexp="^sheet .*")
async def save_worksheet_for_current_user(message: types.Message):
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Тебя нет в системе, сначала набери `/start`", parse_mode=ParseMode.MARKDOWN)
    worksheet = message.text.removeprefix("sheet").strip()
    await chat_service.set_default_worksheet(chat.chat_id, worksheet)
    return await message.answer(f"Привязал worksheet `{worksheet}`", parse_mode=ParseMode.MARKDOWN)


@dispatcher.message_handler()
async def handle_any_message(message: types.Message):
    chat = await chat_service.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Тебя нет в системе, сначала набери `/start`", parse_mode=ParseMode.MARKDOWN)
    if chat.workbook_url is None:
        return await message.answer("Сначала пришли ссылку на workbook, куда сохранять", parse_mode=ParseMode.MARKDOWN)
    await message.answer(text="Пробую понять, что тут...")
    try:
        parsed = parse_rashodik(message.text, chat)
    except ParseError as ex:
        match ex.error:
            case ParseErrorType.NO_AMOUNT:
                return await message.answer(text="Не понял, какая сумма")
            case ParseErrorType.NO_DESCRIPTION:
                return await message.answer(text="Не понял, на что")
            case _:
                raise ex from None

    await wb_service.save_spend(chat, message.date, message.chat.username, parsed)
    response = f"Записал: {parsed.amount} {parsed.currency} {parsed.description}"
    await message.answer(text=response)


def main():
    async def set_bot_commands(disp):
        await disp.bot.set_my_commands(
            commands=[
                BotCommand(
                    command="/start",
                    description="Начать работу",
                ),
                BotCommand(
                    command="/remove",
                    description="Удалить последнюю запись",
                ),
                BotCommand(
                    command="/help",
                    description="Пояснить, как я работаю",
                ),
            ]
        )

    executor.start_polling(
        dispatcher,
        skip_updates=True,
        on_startup=[
            run_alembic_migration,
            set_bot_commands,
        ],
    )


if __name__ == "__main__":
    main()

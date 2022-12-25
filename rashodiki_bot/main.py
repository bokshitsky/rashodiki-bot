from aiogram.types import BotCommand
from aiogram.utils import executor

from rashodiki_bot.handlers import dispatcher, bot
from rashodiki_bot.model import run_alembic_migration


def main():
    async def set_bot_commands(disp):
        await bot.set_my_commands(
            commands=[
                BotCommand(command="/remove", description="Удалить последнюю запись"),
                BotCommand(command="/settings", description="Поменять настройки"),
                BotCommand(command="/start", description="Начать работу"),
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

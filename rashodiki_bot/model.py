from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from alembic import context
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy import Column, BigInteger, Text, DateTime
from sqlalchemy.orm import declarative_base

import rashodiki_bot.db
from rashodiki_bot.settings import settings

Base = declarative_base()

DEFAULT_WORKSHEET = "rashodiki"


class Chat(Base):
    __tablename__ = "chat"
    chat_id: int = Column(BigInteger(), primary_key=True)
    workbook_url: str = Column(Text(), nullable=True)
    worksheet_name: str = Column(Text(), nullable=True)
    default_currency: str = Column(Text(), nullable=True)
    creation_time: datetime = Column(DateTime(True), nullable=False)

    def get_worksheet_name(self):
        return self.worksheet_name or DEFAULT_WORKSHEET


async def run_alembic_migration(*args):
    alembic_config = _load_alembic_config()
    script = ScriptDirectory.from_config(alembic_config)
    destination = "head"

    def upgrade(rev, _):
        return script._upgrade_revs(destination, rev)

    with EnvironmentContext(
        alembic_config,
        script,
        fn=upgrade,
        destination_rev=destination,
    ):
        async with rashodiki_bot.db.engine.connect() as connection:
            await connection.run_sync(_do_run_migrations)


def _do_run_migrations(connection):
    target_metadata = Base.metadata
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def _load_alembic_config():
    app_dir = Path(__file__).parent.parent
    alembic_cfg = Config(str(app_dir.joinpath("alembic.ini")))
    alembic_cfg.set_main_option("script_location", str(app_dir.joinpath("alembic")))
    alembic_cfg.set_main_option("sqlalchemy.url", settings().db_url)
    return alembic_cfg


CURRENCY_LIST = ["рубль", "драм", "доллар", "евро", "лари", "бат", "тенге", "шекель"]


@dataclass
class TransferInfo:
    amount: int
    currency: str
    description: str


class ResponseException(RuntimeError):
    def __init__(self, text, reply=False):
        self.text = text
        self.reply = reply

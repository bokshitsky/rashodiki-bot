from sqlalchemy import Integer, Column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class BotUser(Base):
    __tablename__ = "bot_user"
    tag_id: int = Column(Integer(), primary_key=True)


engine = create_async_engine("sqlite+aiosqlite:///database.db")
Session = sessionmaker(engine, class_=AsyncSession)

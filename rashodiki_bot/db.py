import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import TypeVar, Callable

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.session import _AsyncSessionContextManager
from sqlalchemy.orm import sessionmaker

from rashodiki_bot.settings import settings

_current_session_var: ContextVar[AsyncSession] = ContextVar("_current_session")


class _AsyncSession(AsyncSession):
    async def __aenter__(self):
        self._current_session_var_token = _current_session_var.set(self)
        return await super().__aenter__()

    async def __aexit__(self, type_, value, traceback, reset_session_contextvar=True) -> None:
        await super().__aexit__(type_, value, traceback)
        if reset_session_contextvar:
            _current_session_var.reset(self._current_session_var_token)

    def _maker_context_manager(self):
        return _JagAsyncSessionContextManager(self)


engine = create_async_engine(settings().db_url, echo=False)
Session = sessionmaker(engine, class_=_AsyncSession)


class _JagAsyncSessionContextManager(_AsyncSessionContextManager):
    async def __aenter__(self):
        self.trans = self.async_session.begin()
        await self.trans.__aenter__()
        return await self.async_session.__aenter__()  # Вот здесь отличие от стандартной имплементации

    async def __aexit__(self, type_, value, traceback):
        async def go():
            await self.trans.__aexit__(type_, value, traceback)
            await self.async_session.__aexit__(type_, value, traceback, reset_session_contextvar=False)

        await asyncio.shield(go())
        # Вот здесь отличие от стандартной имплементации
        _current_session_var.reset(self.async_session._current_session_var_token)


def get_current_session(allow_missing=False) -> AsyncSession | None:
    if allow_missing:
        return _current_session_var.get(None)
    return _current_session_var.get()


C = TypeVar("C", bound=Callable)


def transactional(func: C) -> C:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = get_current_session(allow_missing=True)
        if session is None:
            async with Session.begin():
                return await func(*args, **kwargs)
        return await func(*args, **kwargs)

    return wrapper


def with_session(func: C) -> C:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = get_current_session(allow_missing=True)
        if session is None:
            async with Session():
                return await func(*args, **kwargs)
        return await func(*args, **kwargs)

    return wrapper

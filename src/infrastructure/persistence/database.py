import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel


def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(
            f"Variable de entorno '{key}' no encontrada. "
            f"Configura el archivo .env con todas las variables requeridas."
        )
    return value


DB_HOST = _get_required_env("DB_HOST")
DB_PORT = _get_required_env("DB_PORT")
DB_USER = _get_required_env("DB_USER")
DB_PASSWORD = _get_required_env("DB_PASSWORD")
DB_NAME = _get_required_env("DB_NAME")
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

async_session_maker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


from contextlib import asynccontextmanager


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para obtener una sesión fuera de FastAPI dependency injection.

    Uso:
        async with get_session_context() as session:
            repo = SomeRepository(session)
            await repo.do_something()
            await session.commit()
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def close_db_connection() -> None:
    await async_engine.dispose()

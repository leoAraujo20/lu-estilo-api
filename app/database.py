from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL)


async def get_async_session() -> AsyncGenerator[
    AsyncSession
]:  # pragma: no cover
    """Cria uma sessão de banco de dados de forma assíncrona."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

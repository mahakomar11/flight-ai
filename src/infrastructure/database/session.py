from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.config.config import Config


@lru_cache(maxsize=10)
def get_engine(db_url: str) -> AsyncEngine:
    return create_async_engine(
        db_url,
        pool_size=30,
        max_overflow=0,
        pool_pre_ping=True,  # liveness upon each checkout
    )


async def get_session(config: Config):
    engine = get_engine(config.async_postgres_url)

    session_maker = async_sessionmaker(engine)
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        finally:
            await session.rollback()

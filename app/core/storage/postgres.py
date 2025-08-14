from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException


class PostgresDatabase:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
                if session.is_active:
                    await session.commit()
            except DataBaseException:
                await session.rollback()
            finally:
                await session.close()


async def get_session(db_instance: PostgresDatabase) -> AsyncGenerator[AsyncSession, None]:
    async for session in db_instance.get_db():
        yield  session

from typing import AsyncGenerator
from fastapi.concurrency import asynccontextmanager
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine , async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException


class PostgresDatabase:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=15,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        
        self._session_factory = async_sessionmaker(
            bind=self._engine, 
            class_=AsyncSession,
            autocommit=False, 
            autoflush=False, 
            expire_on_commit=False
        )
        
    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    def create_session(self) -> AsyncSession:
        return self._session_factory()

        
async def provide_session(db_instance: PostgresDatabase) -> AsyncGenerator[AsyncSession, None]:
    async with db_instance._session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
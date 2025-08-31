from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine , async_sessionmaker

class PostgresDatabase:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=10,
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
        
    def create_session(self) -> AsyncSession:
        return self._session_factory()

async def create_session(db_instance: PostgresDatabase):
    session = db_instance.create_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
import asyncio
import pytest
from app.core.storage.postgres import PostgresDatabase
from tests.unit.test_settings import test_settings



@pytest.mark.asyncio(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio(scope="module")
async def test_db():
    db = PostgresDatabase(test_settings.POSTGRES_DATABASE_URL)
    await db.init_db()  
    yield db

@pytest.fixture
async def session(test_db):
    async for s in test_db.get_db():
        yield s
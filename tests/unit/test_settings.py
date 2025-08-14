from pydantic_settings import BaseSettings
import pytest

class Settings(BaseSettings):
    POSTGRES_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
def test_settings():
    return Settings() 
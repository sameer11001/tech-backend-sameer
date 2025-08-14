import uuid6
from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.user_management.auth.v1.use_case.UserLogin import UserLogin
from app.core.exceptions.custom_exceptions.InvalidCredentialsException import InvalidCredentialsException
from app.user_management.auth.v1.schemas.response.LoginResponse import LoginResponse

class DummyRequest:
    def __init__(self):
        self.session = {}

@pytest.fixture
def dummy_request():
    return DummyRequest()

@pytest.fixture
def dummy_user():
    user = MagicMock()
    user.id = uuid6.uuid7()
    user.email = "test@example.com"
    user.password = "hashedpassword"  
    user.client_id = 1

    role = MagicMock()
    role.role_name.value = "user"
    user.roles = [role]
    return user


@pytest.fixture
def dummy_client():
    client = MagicMock()
    client.id = 1
    client.client_id = 1
    return client

@pytest.fixture
def dummy_refresh_token():
    token = MagicMock()
    token.id = 1
    token.token = str(uuid6.uuid7())
    token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    token.revoked = False
    return token

# Service Mocks
@pytest.fixture
def user_service(dummy_user):
    service = MagicMock()
    service.get_by_email = AsyncMock(return_value=dummy_user)
    service.get_by_id = AsyncMock(return_value=dummy_user)
    service.update = AsyncMock()
    return service

@pytest.fixture
def client_service(dummy_client):
    service = MagicMock()
    service.get_by_client_id = AsyncMock(return_value=dummy_client)
    return service

@pytest.fixture
def refresh_token_service(dummy_refresh_token):
    service = MagicMock()
    service.create_token = AsyncMock(return_value=dummy_refresh_token)
    return service

@pytest.fixture
def user_login_use_case(user_service, refresh_token_service, client_service):
    return UserLogin(user_service, refresh_token_service, client_service)

def fake_verify_hash(password: str, hashed: str) -> bool:
    return password == "correct"  

import app.user_management.auth.v1.use_case.UserLogin as ul
ul.verify_hash = fake_verify_hash

@pytest.mark.asyncio
async def test_user_login_success(dummy_request, user_login_use_case, dummy_user):
    response = await user_login_use_case.execute(
        request=dummy_request,
        user_email=dummy_user.email,
        user_password="correct", 
        client_id=1
    )
    assert dummy_request.session.get("refresh_token") is not None
    assert dummy_request.session.get("user_id") == str(dummy_user.id)
    assert isinstance(response, LoginResponse)
    assert response.access_token

@pytest.mark.asyncio
async def test_user_login_invalid_password(dummy_request, user_login_use_case, dummy_user):
    with pytest.raises(InvalidCredentialsException):
        await user_login_use_case.execute(
            request=dummy_request,
            user_email=dummy_user.email,
            user_password="wrong", 
            client_id=1
        )
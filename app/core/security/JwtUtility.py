from pathlib import Path
import jwt
import datetime
from typing import Dict
from fastapi import HTTPException, Depends, logger, status
from fastapi.security import HTTPBearer
from jwcrypto import jwk

from app.core.config.settings import settings
from app.core.exceptions.custom_exceptions.GenerateTokenException import GenerateTokenException
from app.core.exceptions.custom_exceptions.InvalidTokenException import InvalidTokenException
from app.core.exceptions.custom_exceptions.TokenExpiredException import TokenExpiredException

oauth2_scheme = HTTPBearer()
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

_PRIVATE_KEY = Path(settings.JWT_PRIVATE_KEY_PATH).read_bytes()

# read the public  key PEM; once
_PUBLIC_KEY  = Path(settings.JWT_PUBLIC_KEY_PATH).read_bytes()


class JwtTokenUtils:
    @staticmethod
    def generate_token(
        username: str,
        user_id: str,
        role: list[str],
        business_profile_id: str
    ) -> str:
        claims: Dict = {
            "sub": username,
            "userId": user_id,
            "role": role,
            "business_profile_id": business_profile_id
        }
        return JwtTokenUtils._create_token(claims)

    @staticmethod
    def _create_token(claims: Dict) -> str:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            claims.update({
                "iat": now,
                "exp": now + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            })
            # sign with your static private PEM
            return jwt.encode(
                claims,
                _PRIVATE_KEY,
                algorithm=settings.JWT_ALGORITHM,
            )
        except Exception as e:
            raise GenerateTokenException(str(e))

    @staticmethod
    def verify_token(token: str) -> Dict:
        try:
            return jwt.decode(
                token,
                _PUBLIC_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException()
        except jwt.InvalidTokenError:
            raise InvalidTokenException()


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    return JwtTokenUtils.verify_token(token.credentials)

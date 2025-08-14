from enum import Enum


class SessionEnum(str, Enum):
    USER_ID = "user_id"
    USER_ROLE = "user_role"
    REFRESH_TOKEN = "refresh_token"

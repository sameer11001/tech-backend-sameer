import re


def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", value):
        raise ValueError("Password must contain at least one number")
    return value


def validate_password_login(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return value

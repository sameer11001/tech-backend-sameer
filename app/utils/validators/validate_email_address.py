import re

def validate_email_address(value: str) -> str:
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if not email_pattern.match(value):
        raise ValueError("Invalid email address.")
    return value

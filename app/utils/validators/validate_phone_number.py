from typing import List
import phonenumbers


def validate_phone_number(value: str) -> str:
    try:
        phone_number = phonenumbers.parse(value, None)
        if not phonenumbers.is_valid_number(phone_number):
            raise ValueError("Invalid phone number format.")
    except phonenumbers.NumberParseException:
        raise ValueError("Invalid phone number format.")
    return value

def validate_phone_list(numbers: List[str]) -> List[str]:
    for num in numbers:
        validate_phone_number(num)  
    return numbers


def validate_country_code(value: str) -> str:

    if not value.startswith("+"):
        raise ValueError("Country code must start with '+'. Example: +962, +1")
    if not value[1:].isdigit():
        raise ValueError("Country code must contain only digits after '+'.")
    return value

def normalize_country_code(value: str) -> str:
    if value.startswith("00"):
        value = "+" + value[2:]
    if not value.startswith("+"):
        raise ValueError("Country code must start with '+' or '00'. Example: +962 or 00962")
    if not value[1:].isdigit():
        raise ValueError("Country code must contain only digits after '+'")
    return value
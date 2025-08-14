import phonenumbers


def validate_phone_number(value: str) -> str:
    try:
        phone_number = phonenumbers.parse(value, None)
        if not phonenumbers.is_valid_number(phone_number):
            raise ValueError("Invalid phone number format.")
    except phonenumbers.NumberParseException:
        raise ValueError("Invalid phone number format.")
    return value

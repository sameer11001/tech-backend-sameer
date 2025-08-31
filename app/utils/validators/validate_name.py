

def validate_names(value):
    if value is None:
        return value
    if not value.strip():
        raise ValueError("Name cannot be empty")
    return value

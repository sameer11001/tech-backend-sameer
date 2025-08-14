from datetime import timezone
from pydantic import AwareDatetime

from app.utils.DateTimeHelper import DateTimeHelper


def validate_utc(dt: AwareDatetime) -> AwareDatetime:
    dt = DateTimeHelper.ensure_utc(dt)
    if dt.tzinfo != timezone.utc:
        raise ValueError("Timestamp must be UTC-aware")
    return dt
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

class DateTimeHelper:
    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)
    
    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            raise ValueError("Datetime string must include timezone info")
        return dt.astimezone(timezone.utc)
    
    @staticmethod
    def to_iso8601(dt: datetime) -> str:
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    @staticmethod
    def to_user_timezone(dt: datetime, tz_name: str) -> datetime:

        return dt.astimezone(ZoneInfo(tz_name))
    
    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        
        return dt.astimezone(timezone.utc)
    
    def enforce_input_is_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            raise ValueError("Naive datetime not allowed—must include timezone")
        if dt.utcoffset() != timezone.utc.utcoffset(dt):
            raise ValueError("Timezone must be UTC")
        return dt
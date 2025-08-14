from datetime import datetime

from pydantic import BaseModel


class TestBroadcast(BaseModel):
    broad_cast_id: str
    date_time: datetime
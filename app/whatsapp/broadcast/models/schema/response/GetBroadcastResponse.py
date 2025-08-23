from typing import List
from app.utils.enums.BroadcastStatus import BroadcastStatus


class BroadCastResponse:
    id: str
    name: str
    scheduled_time: str
    status: BroadcastStatus
    total_contacts: int
    template_id : str

class GetBroadcastResponse:
    broadcasts: List[BroadCastResponse]
    total_count: int
    total_pages: int
    limit: int
    page: int
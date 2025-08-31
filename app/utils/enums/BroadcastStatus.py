from enum import Enum

class BroadcastStatus(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROCESSING = "processing"
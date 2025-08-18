from enum import Enum

class ConversationStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    SOLVED = "solved"
    BRODCAST = "broadcast"
    EXPIRED = "expired"
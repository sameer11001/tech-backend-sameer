from enum import Enum

class ConversationStatus(Enum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    SOLVED = "SOLVED"
    BROADCAST = "BROADCAST" 
    EXPIRED = "EXPIRED" 
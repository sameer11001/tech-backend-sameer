from enum import Enum


class FlowNodeType(str, Enum):
    MESSAGE = "message"
    QUESTION = "question"
    INTERACTIVE_BUTTONS = "interactive_buttons"
    OPERATION = "operation"
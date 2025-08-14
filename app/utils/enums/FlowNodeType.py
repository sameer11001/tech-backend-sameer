from enum import Enum


class FlowNodeType(str, Enum):
    MESSAGE = "message"
    QUESTION = "question"
    QUESTION_WITH_BUTTONS = "question_with_buttons"
    OPERATION = "operation"


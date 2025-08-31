from enum import Enum


class ComponentTypeEnum(str, Enum):
    HEADER  = "HEADER"
    BODY    = "BODY"
    FOOTER  = "FOOTER"
    BUTTONS = "BUTTONS"
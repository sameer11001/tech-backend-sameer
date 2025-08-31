from abc import ABC, abstractmethod
from typing import Any, Dict


class ComponentBuilder(ABC):
    @abstractmethod
    def build(self, data: Any) -> Dict[str,Any]:
        pass
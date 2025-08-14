from abc import ABC, abstractmethod
from typing import Dict, Any

class ComponentBuilder(ABC):
    """Abstract base class for all component builders"""
    
    @abstractmethod
    def build(self, data: Any) -> Dict[str, Any]:
        """Build a component from the provided data"""
        pass
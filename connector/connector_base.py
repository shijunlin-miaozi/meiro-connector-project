from abc import ABC, abstractmethod
from typing import List, Dict

class BaseConnector(ABC):
    """Abstract data source: fetch raw rows and transform to a canonical schema."""
    
    @abstractmethod
    def fetch(self) -> List[Dict]: 
        """Return raw rows from the source system."""
        ...
    
    @abstractmethod
    def transform(self, rows: List[Dict]) -> List[Dict]: 
        """Normalize raw rows to the project's canonical schema."""
        ...


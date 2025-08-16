from abc import ABC, abstractmethod
from typing import List, Dict

class BaseUploader(ABC):
    """"Abstract destination that receives normalized rows for delivery."""
    
    @abstractmethod
    def upload(self, rows: List[Dict]) -> None:
        """Deliver rows to the destination, raising on failure."""
        ...

from abc import ABC, abstractmethod
from typing import Dict, Any

class BankAdapterInterface(ABC):
    @abstractmethod
    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        pass

    @abstractmethod
    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw provider payload into Universal Normalized Event Format.
        """
        pass

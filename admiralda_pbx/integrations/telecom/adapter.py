from abc import ABC, abstractmethod
from typing import Dict, Any

class TelephonyAdapter(ABC):
    """
    Interface for telephony providers.
    """
    @abstractmethod
    async def ingest_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def initiate_outbound(self, to_number: str, message: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def handle_call_event(self, event_type: str, call_id: str, payload: Dict[str, Any]) -> None:
        pass

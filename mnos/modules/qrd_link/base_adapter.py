from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseDroneAdapter(ABC):
    @abstractmethod
    async def connect(self, connection_str: str):
        pass

    @abstractmethod
    async def arm(self):
        pass

    @abstractmethod
    async def takeoff(self, altitude: float):
        pass

    @abstractmethod
    async def dispatch(self, location: tuple):
        pass

    @abstractmethod
    async def return_to_base(self):
        pass

    @abstractmethod
    async def get_telemetry(self) -> Dict[str, Any]:
        pass

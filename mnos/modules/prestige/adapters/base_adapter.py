from typing import Dict, List

class BaseHotelAdapter:
    def __init__(self, name: str):
        self.name = name

    async def get_rates(self, query: Dict) -> List[Dict]:
        """
        Adapters are supply-only.
        They provide rates, availability, etc.
        They DO NOT write to SHADOW, execute UPOS, or lock FCE.
        """
        raise NotImplementedError("Subclasses must implement get_rates")

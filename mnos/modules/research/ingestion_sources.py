from typing import List

class IngestionSources:
    """
    eLEGAL v0.3: Research Ingestion Sources.
    """
    def list_active_sources(self) -> List[str]:
        return ["MVLAW_PUBLIC", "GOVT_GAZETTE", "BUSINESS_PORTAL"]

ingestion_sources = IngestionSources()

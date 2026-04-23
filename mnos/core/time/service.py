import time
from datetime import datetime, timezone

class SovereignTime:
    """
    Core Time: Signed and Attested.
    Ensures dual timestamps for every system event.
    """
    def get_attested_time(self):
        """Returns dual timestamp with simulated PTP/NTP signature."""
        now = datetime.now(timezone.utc)
        return {
            "event_time": now.isoformat(),
            "ingest_time": now.isoformat(),
            "ptp_signature": "SIG_PTP_HARDENED_2026",
            "source": "MIG-ATTESTED-CLOCK-01"
        }

sovereign_time = SovereignTime()

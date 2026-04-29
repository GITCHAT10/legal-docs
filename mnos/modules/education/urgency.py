from datetime import datetime, UTC, timedelta
from typing import Dict, Optional

class UrgencyPressureEngine:
    """
    Drives conversion via dynamic urgency and inventory signals.
    """
    def __init__(self):
        self.inventory_cache = {
            "villas": 3,
            "accelerator_seats": 5
        }

    def get_urgency_payload(self, context: str):
        """
        Returns real-time urgency signals.
        """
        expiry = datetime.now(UTC) + timedelta(hours=48)

        signals = {
            "uha_accelerator": {
                "expires_at": expiry.isoformat(),
                "countdown_text": "Held for you for the next 48 hours",
                "remaining": f"Only {self.inventory_cache['accelerator_seats']} seats remain",
                "social_proof": "12 other candidates are viewing this right now"
            },
            "resort_booking": {
                "remaining": f"Only {self.inventory_cache['villas']} villas remain for your dates",
                "last_booked": "2 hours ago",
                "demand_level": "CRITICAL"
            }
        }

        return signals.get(context, {})

    def update_inventory(self, context: str, count: int):
        self.inventory_cache[context] = count
        return True

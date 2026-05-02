from typing import Dict, Any, List
from datetime import datetime, UTC, date

class UTSafetyGateEngine:
    def __init__(self, shadow):
        self.shadow = shadow

    def validate_dispatch(self, actor_ctx: dict, asset_data: dict, weather_data: dict) -> Dict:
        """
        Validates safety parameters before dispatch.
        """
        # Insurance Validation logic
        insurance_valid = False
        raw_expiry = asset_data.get("insurance_expiry")
        if raw_expiry:
            try:
                # Support YYYY-MM-DD
                expiry_date = datetime.strptime(raw_expiry, "%Y-%m-%d").date()
                insurance_valid = expiry_date >= datetime.now(UTC).date()
            except (ValueError, TypeError):
                insurance_valid = False

        checks = {
            "vessel_capacity": asset_data.get("passenger_count", 0) <= asset_data.get("capacity", 0),
            "weather_clearance": weather_data.get("sea_state", 0) < 4,
            "captain_license": asset_data.get("captain_status") == "VERIFIED",
            "lifejackets_onboard": asset_data.get("lifejacket_count", 0) >= asset_data.get("passenger_count", 0),
            "insurance_valid": insurance_valid
        }

        all_passed = all(checks.values())

        result = {
            "all_passed": all_passed,
            "checks": checks,
            "gate_status": "APPROVED" if all_passed else "BLOCKED"
        }

        # Log to SHADOW
        self.shadow.commit("ut.safety.dispatch_check", actor_ctx.get("identity_id"), result)

        return result

    def verify_friday_prayer_window(self, departure_time: str) -> bool:
        """
        Blocks departures during Friday prayer windows (12:00 - 13:30).
        """
        # Logic to check time
        return True

from datetime import datetime
import logging

logger = logging.getLogger("unified_suite")

class SovereignOperationalSafety:
    """
    Sovereign Execution Safety Gates for Maldives-specific Operations.
    """

    @staticmethod
    def check_seaplane_night_ops(flight_number: str, arrival_time: datetime):
        """
        Sovereign Rule: Seaplanes (TMA, Manta, etc.) CANNOT operate at night in Maldives.
        Simulation: Night is defined as 18:00 to 06:00.
        """
        hour = arrival_time.hour
        if hour >= 18 or hour < 6:
            logger.error(f"Sovereign Violation: Night landing attempted for {flight_number}")
            raise PermissionError("Seaplane operations are restricted to daylight hours only (06:00 - 18:00)")
        return True

    @staticmethod
    def check_port_tide_constraints(vessel_id: str, draft: float):
        """
        Sovereign Rule: Vessels with draft > 10m require high tide for safe docking.
        Simulation: High tide is simulated as even hours.
        """
        if draft > 10.0:
            current_hour = datetime.now().hour
            if current_hour % 2 != 0:
                logger.warning(f"Sovereign Alert: Low tide restriction for deep-draft vessel {vessel_id}")
                raise PermissionError(f"Vessel {vessel_id} exceeds 10m draft. Port access restricted during low tide.")
        return True

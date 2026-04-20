import logging
from ..models import WeatherStatus

logger = logging.getLogger("unified_suite")

class AtollIntegrations:
    """
    Handles external resort and weather synchronization.
    """

    @staticmethod
    def get_resort_status(resort_id: str) -> bool:
        """
        Mock Resort Sync: Checks if resort is 'Guest Ready'.
        In a real system, this would call a resort management API.
        """
        # Simulate: Most resorts are ready, but some are not
        is_ready = resort_id != "RESORT_MAINTENANCE"
        if is_ready:
            logger.info(f"Resort Sync: {resort_id} reported GUEST_READY")
        else:
            logger.warning(f"Resort Sync: {resort_id} reported NOT_READY")
        return is_ready

    @staticmethod
    def get_weather(location_id: str) -> WeatherStatus:
        """
        Mock Weather Sync: Fetches current lagoon weather.
        """
        # Standard tropical weather
        return WeatherStatus(
            location_id=location_id,
            wind_speed_knots=12.5,
            wind_direction=270, # West
            visibility_meters=10000.0
        )

from ..models import WaterZone, WaterLane, WeatherStatus
from typing import List, Optional
import logging

logger = logging.getLogger("unified_suite")

class LagoonRunwayEngine:
    """
    Manages takeoff and landing lanes in Maldives water zones.
    """

    @staticmethod
    def assign_best_lane(zone: WaterZone, weather: WeatherStatus) -> Optional[WaterLane]:
        """
        Assigns the best takeoff/landing lane based on wind direction.
        Seaplanes must take off/land into the wind.
        """
        if weather.wind_speed_knots > 25:
            logger.warning(f"Weather Restriction: Wind speed {weather.wind_speed_knots} exceeds safe limit for {zone.zone_id}")
            return None

        if weather.visibility_meters < 500:
            logger.warning(f"Weather Restriction: Visibility {weather.visibility_meters} below minimum for {zone.zone_id}")
            return None

        best_lane = None
        min_diff = 360

        for lane in zone.lanes:
            if lane.status != "OPEN":
                continue

            # Wind is blowing FROM wind_direction. Seaplane heads INTO wind.
            # Heading should ideally match wind_direction.
            diff = abs(lane.heading - weather.wind_direction)
            diff = min(diff, 360 - diff)

            if diff < min_diff:
                min_diff = diff
                best_lane = lane

        if best_lane:
            logger.info(f"Lagoon Engine: Assigned lane {best_lane.lane_id} in {zone.zone_id} (Wind: {weather.wind_direction}, Heading: {best_lane.heading})")

        return best_lane

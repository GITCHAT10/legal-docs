from ..models import SeaplaneFlight
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("unified_suite")

class RotationScheduler:
    """
    Optimizes seaplane aircraft usage through auto-looping rotations.
    Goal: 10-15 cycles per aircraft per day.
    """

    @staticmethod
    def create_daily_rotation(aircraft_id: str, base: str, destinations: List[str]) -> List[SeaplaneFlight]:
        """
        Generates a continuous loop of flights for a single aircraft.
        Example: Base -> Resort A -> Base -> Resort B -> Base...
        """
        rotation = []
        current_time = datetime.now().replace(hour=6, minute=0, second=0) # Start of Maldivian seaplane day

        # 12 cycles per day (standard seaplane capacity)
        for i in range(12):
            dest = destinations[i % len(destinations)]

            # Leg 1: Base to Resort
            f1_id = f"ROT_{aircraft_id}_{i}_A"
            flight_to = SeaplaneFlight(
                flight_id=f1_id,
                aircraft_id=aircraft_id,
                origin=base,
                destination=dest,
                scheduled_departure=current_time
            )
            rotation.append(flight_to)

            current_time += timedelta(minutes=45) # Flight + Turnaround

            # Leg 2: Resort to Base
            f2_id = f"ROT_{aircraft_id}_{i}_B"
            flight_back = SeaplaneFlight(
                flight_id=f2_id,
                aircraft_id=aircraft_id,
                origin=dest,
                destination=base,
                scheduled_departure=current_time
            )
            rotation.append(flight_back)

            current_time += timedelta(minutes=45)

        logger.info(f"Rotation Scheduler: Generated {len(rotation)} flight sectors for aircraft {aircraft_id}")
        return rotation

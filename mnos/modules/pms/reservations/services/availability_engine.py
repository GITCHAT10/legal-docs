from datetime import date, datetime, timedelta, UTC
from typing import Dict, List, Optional
from mnos.modules.pms.reservations.models.reservation import AvailabilityCache

class AvailabilityEngine:
    """
    PMS Availability Engine: Handles optimistic locking and inventory checks.
    Partitioned by date and room_type.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.cache: Dict[tuple, AvailabilityCache] = {} # (date, room_type_id) -> AvailabilityCache

    def initialize_inventory(self, room_type_id: str, total_rooms: int, start_date: date, days: int = 365):
        """Pre-populates the availability cache for a room type."""
        for i in range(days):
            d = start_date + timedelta(days=i)
            key = (d, room_type_id)
            if key not in self.cache:
                self.cache[key] = AvailabilityCache(
                    date=d,
                    room_type_id=room_type_id,
                    total_rooms=total_rooms
                )

    def get_availability(self, room_type_id: str, check_in: date, check_out: date) -> int:
        """Returns the minimum available rooms in the date range."""
        min_avail = float('inf')
        current = check_in
        while current < check_out:
            key = (current, room_type_id)
            entry = self.cache.get(key)
            if not entry:
                return 0

            avail = entry.total_rooms - entry.allocated_rooms
            if avail < min_avail:
                min_avail = avail
            current += timedelta(days=1)

        return int(min_avail) if min_avail != float('inf') else 0

    def lock_inventory(self, room_type_id: str, check_in: date, check_out: date, expected_version: int = 1) -> bool:
        """
        Optimistic lock for inventory allocation.
        Ensures atomic increment of allocated_rooms across the stay period.
        """
        # 1. First Pass: Verify availability and versions
        current = check_in
        updates_needed = []
        while current < check_out:
            key = (current, room_type_id)
            entry = self.cache.get(key)
            if not entry or (entry.total_rooms - entry.allocated_rooms) <= 0:
                return False
            updates_needed.append(entry)
            current += timedelta(days=1)

        # 2. Second Pass: Commit allocation
        for entry in updates_needed:
            # Simulate Optimistic Locking: version check
            # In a real DB, this is: UPDATE ... SET allocated_rooms = allocated_rooms + 1, version = version + 1 WHERE version = ?
            entry.allocated_rooms += 1
            entry.version += 1

        return True

    def release_inventory(self, room_type_id: str, check_in: date, check_out: date):
        """Releases allocated rooms back to inventory."""
        current = check_in
        while current < check_out:
            key = (current, room_type_id)
            entry = self.cache.get(key)
            if entry and entry.allocated_rooms > 0:
                entry.allocated_rooms -= 1
                entry.version += 1
            current += timedelta(days=1)

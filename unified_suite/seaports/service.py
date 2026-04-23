from .models import Vessel, Container
from typing import List
import logging
import threading

logger = logging.getLogger("unified_suite")

class SeaPortService:
    def __init__(self):
        self.vessels = []
        self.berths = [f"BERTH_{i}" for i in range(1, 6)]
        self._lock = threading.Lock()

    def register_vessel(self, vessel: Vessel):
        with self._lock:
            existing = next((v for v in self.vessels if v.vessel_id == vessel.vessel_id), None)
            if existing:
                logger.info(f"Idempotency: vessel {vessel.vessel_id} already registered")
                return existing
            self.vessels.append(vessel)
            return vessel

    def assign_berth(self, vessel):
        with self._lock:
            # Compatibility: handle vessel object or vessel_id string
            vessel_obj = vessel
            if isinstance(vessel, str):
                vessel_obj = next((v for v in self.vessels if v.vessel_id == vessel), None)
                if not vessel_obj:
                    return None

            # ✅ Idempotency: preserve existing assignment
            if vessel_obj.berth:
                logger.info(f"Idempotency: preserving existing berth {vessel_obj.berth} for vessel {vessel_obj.vessel_id}")
                return vessel_obj.berth

            used_berths = [v.berth for v in self.vessels if v.berth]

            for berth in self.berths:
                if berth not in used_berths:
                    vessel_obj.berth = berth
                    vessel_obj.status = "DOCKED"
                    logger.info(f"New assignment: vessel {vessel_obj.vessel_id} assigned to {berth}")
                    return berth

            logger.error(f"Assignment failed: no berths available for vessel {vessel_obj.vessel_id}")
            raise Exception("No berths available")

    def get_vessel_manifest(self, vessel_id: str) -> List[Container]:
        for vessel in self.vessels:
            if vessel.vessel_id == vessel_id:
                return vessel.containers
        return []

    def get_all_vessels(self) -> List[Vessel]:
        return self.vessels

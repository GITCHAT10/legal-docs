from .models import Vessel, Container
from typing import List

class SeaPortService:
    def __init__(self):
        self.vessels = []
        self.berths = [f"BERTH_{i}" for i in range(1, 6)]

    def register_vessel(self, vessel: Vessel):
        self.vessels.append(vessel)
        return vessel

    def assign_berth(self, vessel_id: str):
        for vessel in self.vessels:
            if vessel.vessel_id == vessel_id:
                # IDEMPOTENCY: Do not reassign if already assigned
                if vessel.berth:
                    return vessel.berth

                used_berths = [v.berth for v in self.vessels if v.berth]
                for berth in self.berths:
                    if berth not in used_berths:
                        vessel.berth = berth
                        vessel.status = "DOCKED"
                        return berth
        return None

    def get_vessel_manifest(self, vessel_id: str) -> List[Container]:
        for vessel in self.vessels:
            if vessel.vessel_id == vessel_id:
                return vessel.containers
        return []

    def get_all_vessels(self) -> List[Vessel]:
        return self.vessels

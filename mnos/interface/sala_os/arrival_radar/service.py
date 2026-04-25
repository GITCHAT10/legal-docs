from typing import Dict, Any, List
from mnos.modules.atc_tower.service import atc_tower
from mnos.modules.crmlab.service import crmlab

class ArrivalRadarService:
    """
    SALA Arrival Radar: Maps ATC events to guest records.
    Enforces mission-scope 'V1' confirmed linkage.
    """
    def get_radar_view(self, session_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieves radar data and performs guest record mapping.
        """
        if session_context.get("mission_scope") != "V1":
             raise RuntimeError("ARRIVAL_RADAR: Access denied. Mission Scope 'V1' required.")

        raw_radar = atc_tower.get_arrival_radar_data()

        # Perform mapping simulation
        mapped_view = []
        for craft in raw_radar:
            guest_id = f"G-{craft['id'][-3:]}"
            guest = crmlab.get_guest_record(guest_id)

            mapped_view.append({
                "craft_id": craft["id"],
                "type": craft["type"],
                "eta": craft["eta"],
                "origin": craft["origin"],
                "linked_guest": guest["name"] if guest else "UNKNOWN (OPS ALERT ONLY)"
            })

        return mapped_view

arrival_radar_service = ArrivalRadarService()

from typing import Dict, Any, List, Optional
from mnos.modules.prestige.logistics.access_point_schema import AccessPoint, AccessPointType

class TransferVillaSync:
    def determine_arrival_point(self, guest_privacy: str, vessel_type: str, access_points: List[AccessPoint]) -> Optional[AccessPoint]:
        """
        Logic:
        - P4 + private yacht/speedboat must prefer direct docking or bypass route
        - reject main lobby-only route for P4 unless human override
        """
        # Sort access points by preference for P3/P4
        if guest_privacy in ["P3", "P4"]:
            # Prefer Private Villa Jetty or Marina/Bypass
            for ap in access_points:
                if ap.access_point_type == AccessPointType.PRIVATE_VILLA_JETTY and ap.direct_docking_available:
                    return ap
                if ap.p4_bypass_feasible and guest_privacy == "P4":
                    return ap

            # Reject lobby-only
            available = [ap for ap in access_points if ap.access_point_type != AccessPointType.HOTEL_LOBBY]
            if available: return available[0]

        return access_points[0] if access_points else None

    def get_ut_payload(self, access_point: AccessPoint) -> Dict[str, Any]:
        # Send access_point_gps to UT, not public guest brief
        return {
            "target_gps": access_point.access_point_gps,
            "docking_type": access_point.access_point_type,
            "security_clearance_required": access_point.security_entry_point_id is not None
        }

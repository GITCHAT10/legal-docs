from typing import Dict, Any
from mnos.modules.prestige.logistics.access_point_schema import AccessPoint, AccessPointType

class ArrivalProtocolEngine:
    def resolve_arrival_route(self, planned_point: AccessPoint, weather_status: str) -> AccessPoint:
        """
        - if weather feasibility RED and beach landing planned, force Service Quay fallback
        - do not confirm arrival directly
        """
        if weather_status == "RED" and planned_point.access_point_type == AccessPointType.BEACH_LANDING:
            # Look for Service Quay fallback or general fallback
            return planned_point # In a real implementation we would fetch the fallback object by ID

        return planned_point

    def get_security_protocol(self, access_point: AccessPoint) -> Dict[str, Any]:
        # map security/staff entry separately
        return {
            "entry_point": access_point.security_entry_point_id or "MAIN_SECURITY",
            "protocol": "SILENT_PASS" if access_point.p4_bypass_feasible else "STANDARD_CHECK"
        }

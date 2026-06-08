from pydantic import BaseModel
from enum import Enum
from typing import Optional

class AccessPointType(str, Enum):
    MAIN_JETTY = "MAIN_JETTY"
    PRIVATE_VILLA_JETTY = "PRIVATE_VILLA_JETTY"
    SERVICE_QUAY = "SERVICE_QUAY"
    BEACH_LANDING = "BEACH_LANDING"
    SEAPLANE_PLATFORM = "SEAPLANE_PLATFORM"
    MARINA = "MARINA"
    HOTEL_LOBBY = "HOTEL_LOBBY"

class AccessPoint(BaseModel):
    access_point_id: str
    access_point_gps: str # Lat,Long
    access_point_type: AccessPointType
    direct_docking_available: bool = False
    p3_bypass_feasible: bool = False
    p4_bypass_feasible: bool = False
    buggy_requirement: bool = True
    host_meeting_point: str
    security_entry_point_id: Optional[str] = None
    privacy_breach_risk_level: str = "LOW"
    weather_fallback_access_point_id: Optional[str] = None

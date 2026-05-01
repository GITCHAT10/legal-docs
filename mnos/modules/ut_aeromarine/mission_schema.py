from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid

class MissionType(Enum):
    QRD_RESPONSE = "QRD_RESPONSE"
    RESORT_PATROL = "RESORT_PATROL"
    REEF_SURVEY = "REEF_SURVEY"
    ISLAND_MAPPING = "ISLAND_MAPPING"
    MARINE_LOGISTICS = "MARINE_LOGISTICS"
    SEARCH_AND_RESCUE = "SEARCH_AND_RESCUE"
    SECURITY_SWEEP = "SECURITY_SWEEP"
    BOAT_ESCORT = "BOAT_ESCORT"
    INFRASTRUCTURE_INSPECTION = "INFRASTRUCTURE_INSPECTION"
    ENVIRONMENTAL_MONITORING = "ENVIRONMENTAL_MONITORING"

class MissionStatus(Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    READY = "READY"
    LAUNCHED = "LAUNCHED"
    IN_PROGRESS = "IN_PROGRESS"
    RECOVERY = "RECOVERY"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    SHADOW_SEALED = "SHADOW_SEALED"
    BILLING_RELEASED = "BILLING_RELEASED"

class AssetType(Enum):
    QRD_DRONE = "QRD_DRONE"
    DJI_ENTERPRISE_DRONE = "DJI_ENTERPRISE_DRONE"
    PX4_VEHICLE = "PX4_VEHICLE"
    ARDUPILOT_HYBRID_VTOL = "ARDUPILOT_HYBRID_VTOL"
    MULTIROTOR = "MULTIROTOR"
    FIXED_WING = "FIXED_WING"
    USV = "USV"
    ROV = "ROV"
    BOAT_LAUNCHED_DRONE = "BOAT_LAUNCHED_DRONE"
    EMERGENCY_DRONE = "EMERGENCY_DRONE"
    MAPPING_DRONE = "MAPPING_DRONE"

class LaunchPlatform(Enum):
    ISLAND_PAD = "ISLAND_PAD"
    RESORT_JETTY = "RESORT_JETTY"
    BOAT = "BOAT"
    PATROL_VESSEL = "PATROL_VESSEL"
    DOCKING_BOX = "DOCKING_BOX"
    MOBILE_COMMAND_UNIT = "MOBILE_COMMAND_UNIT"
    AIRCLOUD_EDGE_NODE = "AIRCLOUD_EDGE_NODE"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class UTAMMission:
    mission_id: str = field(default_factory=lambda: f"UTAM-{uuid.uuid4().hex[:8].upper()}")
    mission_type: MissionType = MissionType.QRD_RESPONSE
    operator_id: Optional[str] = None
    device_id: Optional[str] = None
    asset_type: AssetType = AssetType.QRD_DRONE
    launch_platform: LaunchPlatform = LaunchPlatform.ISLAND_PAD
    launch_location: tuple = (0.0, 0.0)
    recovery_location: tuple = (0.0, 0.0)
    dynamic_home_point_enabled: bool = False
    airspace_clearance_id: Optional[str] = None
    mndf_approval_ref: Optional[str] = None
    caa_approval_ref: Optional[str] = None
    route_plan: Optional[List[tuple]] = None
    altitude_limit: float = 120.0
    geofence_zone: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.LOW
    commercial_billable: bool = False
    shadow_trace_id: Optional[str] = None
    status: MissionStatus = MissionStatus.DRAFT
    telemetry_required: bool = True
    edge_cache_enabled: bool = False
    emergency_priority: bool = False
    kpi_profile: str = "3-30-3"

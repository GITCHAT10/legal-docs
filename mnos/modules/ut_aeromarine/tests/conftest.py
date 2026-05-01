import pytest
import os
from main import app, guard, shadow_core, identity_core, fce_core, events_core
from mnos.modules.ut_aeromarine.mission_schema import MissionType, AssetType, MissionStatus
from mnos.modules.ut_aeromarine.device_registry import DeviceRegistry
from mnos.modules.ut_aeromarine.operator_authority import OperatorAuthority
from mnos.modules.ut_aeromarine.compliance_gate import ComplianceGate
from mnos.modules.ut_aeromarine.shadow_logger import ShadowLogger
from mnos.modules.ut_aeromarine.telemetry_watchdog import TelemetryWatchdog
from mnos.modules.ut_aeromarine.mission_planner import MissionPlanner
from mnos.modules.ut_aeromarine.fce_billing_gate import FCEBillingGate

@pytest.fixture
def utam_stack():
    # Setup AEGIS identity for MIG-ADMIN-01 if missing
    if "MIG-ADMIN-01" not in identity_core.profiles:
        identity_core.profiles["MIG-ADMIN-01"] = {"profile_type": "admin"}

    registry = DeviceRegistry(shadow_core)
    authority = OperatorAuthority(identity_core)
    shadow_log = ShadowLogger(shadow_core, guard)
    watchdog = TelemetryWatchdog(shadow_core)
    planner = MissionPlanner(ComplianceGate(authority, registry, shadow_core), shadow_log, watchdog, events_core)
    billing = FCEBillingGate(fce_core, shadow_core)

    # Register a test device
    registry.register_device("QRD-UTAM-01", {"type": "DRONE"})

    return planner, registry, authority, watchdog, billing

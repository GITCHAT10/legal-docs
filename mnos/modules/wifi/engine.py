import uuid
from datetime import datetime, UTC, timedelta

class UWiFiEngine:
    """
    U-WiFi Engine: Managed connectivity for iMOXON.UPOS.
    Handles Hotel, Resort, Island, Event, and Marine WiFi.
    """
    def __init__(self, upos_core):
        self.upos = upos_core
        self.routers = {}
        self.profiles = {} # tenant_id -> list of profiles
        self.vessels = {}  # vessel_id -> profile
        self.active_sessions = {}
        self.packages = {
            "free_basic": {"price": 0.0, "bandwidth": "5Mbps"},
            "premium_speed": {"price": 150.0, "bandwidth": "50Mbps"},
            "business_speed": {"price": 500.0, "bandwidth": "100Mbps"},
            "event_wifi": {"price": 2500.0, "bandwidth": "Dedicated"},
            "marine_pass": {"price": 250.0, "bandwidth": "Satellite"}
        }

    # --- CORE MGMT ---

    def register_router(self, actor_ctx: dict, router_data: dict):
        return self.upos.execute_transaction(
            "wifi.router.register",
            actor_ctx,
            self._internal_register_router,
            router_data
        )

    def _internal_register_router(self, data):
        router_id = f"WIFI-{uuid.uuid4().hex[:6].upper()}"
        router = {
            "id": router_id,
            "model": data.get("model", "WAVLINK AX1800"),
            "location": data.get("location"),
            "status": "ONLINE",
            "firmware": "v1.0.0-SALA",
            "last_check": datetime.now(UTC).isoformat()
        }
        self.routers[router_id] = router
        return router

    def create_property_profile(self, actor_ctx: dict, profile_data: dict):
        return self.upos.execute_transaction(
            "wifi.profile.create",
            actor_ctx,
            self._internal_create_profile,
            profile_data
        )

    def _internal_create_profile(self, data):
        tenant_id = data.get("tenant_id")
        profile_id = f"PROF-{uuid.uuid4().hex[:6].upper()}"
        profile = {
            "id": profile_id,
            "tenant_id": tenant_id,
            "property_id": data.get("property_id"),
            "island": data.get("island"),
            "SSID": data.get("SSID", "U-WiFi-Guest"),
            "networks": ["guest", "staff", "operations", "pos", "cctv"],
            "WAN_primary": data.get("WAN_primary", "Fiber"),
            "WAN_backup": data.get("WAN_backup", "Starlink"),
            "captive_portal": True
        }
        if tenant_id not in self.profiles:
            self.profiles[tenant_id] = []
        self.profiles[tenant_id].append(profile)
        return profile

    # --- MARINE MGMT ---

    def register_vessel_wifi(self, actor_ctx: dict, vessel_data: dict):
        return self.upos.execute_transaction(
            "wifi.marine.register",
            actor_ctx,
            self._internal_register_vessel,
            vessel_data
        )

    def _internal_register_vessel(self, data):
        vessel_id = data.get("vessel_id")
        vessel_profile = {
            "vessel_id": vessel_id,
            "vessel_name": data.get("vessel_name"),
            "vessel_type": data.get("vessel_type"),
            "WAN_options": ["Starlink_Maritime", "4G_SIM", "Harbor_WiFi"],
            "current_WAN": "Starlink_Maritime",
            "status": "DOCK_MODE"
        }
        self.vessels[vessel_id] = vessel_profile
        return vessel_profile

    # --- WORKFLOWS ---

    def issue_guest_access(self, actor_ctx: dict, guest_data: dict):
        """
        Captive portal entry or room-based trigger.
        """
        return self.upos.execute_transaction(
            "wifi.access.issue",
            actor_ctx,
            self._internal_issue_access,
            guest_data
        )

    def _internal_issue_access(self, data):
        access_id = f"ACC-{uuid.uuid4().hex[:8].upper()}"
        pkg_name = data.get("package", "free_basic")
        pkg = self.packages.get(pkg_name)

        session = {
            "id": access_id,
            "guest_id": data.get("guest_id"),
            "room_id": data.get("room_id"),
            "vessel_id": data.get("vessel_id"),
            "package": pkg_name,
            "bandwidth": pkg["bandwidth"],
            "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "status": "ACTIVE"
        }
        self.active_sessions[access_id] = session

        # If premium, trigger UPOS billing intent (simulated here)
        if pkg["price"] > 0:
            self.upos.shadow.commit("wifi.payment.intent", data.get("guest_id"), {"amount": pkg["price"]})

        return session

    def trigger_failover(self, actor_ctx: dict, router_id: str, reason: str):
        return self.upos.execute_transaction(
            "wifi.failover.trigger",
            actor_ctx,
            self._internal_failover,
            router_id, reason
        )

    def _internal_failover(self, router_id, reason):
        router = self.routers.get(router_id)
        if not router:
            raise ValueError("Router not found")

        router["wan_status"] = "BACKUP_ACTIVE"
        router["failover_reason"] = reason

        self.upos.events.publish("wifi.failover_active", {"router_id": router_id, "reason": reason})
        return router

    # --- SECURITY ---

    def perform_security_audit(self, actor_ctx: dict, router_id: str):
        return self.upos.execute_transaction(
            "wifi.security.audit",
            actor_ctx,
            self._internal_audit,
            router_id
        )

    def _internal_audit(self, router_id):
        # Simulation of network segmentation check
        return {
            "router_id": router_id,
            "segmentation_check": "PASSED",
            "guest_isolation": "ENABLED",
            "pos_network_secure": "TRUE",
            "timestamp": datetime.now(UTC).isoformat()
        }

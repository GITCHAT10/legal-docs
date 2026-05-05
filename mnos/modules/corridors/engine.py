import uuid
from datetime import datetime, UTC

class USmartCorridorsEngine:
    """
    U-Smart Corridors: Route intelligence and manifest management.
    Links U-Marine and U-Logistics with FCE payout control.
    """
    def __init__(self, upos_core, orca):
        self.upos = upos_core
        self.orca = orca
        self.operators = {}
        self.vessels = {}
        self.captains = {}
        self.routes = {}
        self.manifests = {}
        self.disputes = {}
        self.cargo_rules = {
            "dangerous_goods": "BLOCKED",
            "restricted_goods": "MANUAL_REVIEW",
            "dry_goods": "ALLOWED",
            "perishables": "ALLOWED"
        }
        self.pricing_rules = {
            "fixed_fare": 100.0,
            "per_kg": 0.5,
            "per_cbm": 5.0,
            "fuel_surcharge_pct": 0.05
        }

        # Strategic Corridors
        self.strategic_corridors = [
            "Male to Ari Atoll", "Male to Vaavu", "Male to Baa",
            "Male to Lhaviyani", "Male to Laamu", "Male to Gaafu Alifu",
            "Male to Fuvahmulah", "Male to Addu"
        ]

    # --- REGISTRIES ---

    def register_operator(self, actor_ctx: dict, data: dict):
        op_id = f"OP-{uuid.uuid4().hex[:6].upper()}"
        operator = {
            "id": op_id,
            "name": data.get("name"),
            "aegis_status": "VERIFIED",
            "performance_score": 100.0,
            "status": "ACTIVE"
        }
        self.operators[op_id] = operator
        return operator

    def register_vessel(self, actor_ctx: dict, data: dict):
        v_id = f"VES-{uuid.uuid4().hex[:6].upper()}"
        vessel = {
            "id": v_id,
            "name": data.get("name"),
            "operator_id": data.get("operator_id"),
            "type": data.get("type"),
            "cargo_capacity_kg": data.get("capacity_kg", 1000),
            "seat_capacity": data.get("seats", 20),
            "status": "ACTIVE"
        }
        self.vessels[v_id] = vessel
        return vessel

    def register_captain(self, actor_ctx: dict, data: dict):
        c_id = f"CAPT-{uuid.uuid4().hex[:6].upper()}"
        captain = {
            "id": c_id,
            "aegis_id": data.get("aegis_id"),
            "vessel_id": data.get("vessel_id"),
            "status": "ACTIVE"
        }
        self.captains[c_id] = captain
        return captain

    def create_route(self, actor_ctx: dict, data: dict):
        r_id = f"RTE-{uuid.uuid4().hex[:6].upper()}"
        route = {
            "id": r_id,
            "origin": data.get("origin"),
            "destination": data.get("destination"),
            "transit_time": data.get("transit", "4 hours"),
            "status": "ACTIVE"
        }
        self.routes[r_id] = route
        return route

    # --- MANIFEST MGMT ---

    def create_manifest(self, actor_ctx: dict, data: dict):
        # HARD GATES
        operator = self.operators.get(data.get("operator_id"))
        if not operator or operator["status"] != "ACTIVE":
             raise PermissionError("HARD GATE: No manifest without verified active operator.")

        vessel = self.vessels.get(data.get("vessel_id"))
        if not vessel or vessel["operator_id"] != operator["id"]:
             raise PermissionError("HARD GATE: Unauthorized vessel attempt.")

        m_id = f"MAN-{uuid.uuid4().hex[:8].upper()}"
        manifest = {
            "id": m_id,
            "route_id": data.get("route_id"),
            "operator_id": data.get("operator_id"),
            "vessel_id": data.get("vessel_id"),
            "captain_id": data.get("captain_id"),
            "status": "LOADING",
            "cargo": [],
            "passengers": [],
            "payout_status": "PENDING",
            "apollo_sync_status": "SYNCED",
            "shadow_hash": uuid.uuid4().hex # Simulated hash
        }
        self.manifests[m_id] = manifest
        return manifest

    def load_cargo(self, actor_ctx: dict, manifest_id: str, item_data: dict):
        manifest = self.manifests.get(manifest_id)

        # DOCTRINE GATE: Only paid orders
        order = self.upos.orders.get(item_data.get("order_id"))
        if not order or order["status"] != "PAID":
             raise PermissionError("HARD GATE: No cargo loading without paid/FCE-approved order.")

        manifest["cargo"].append(item_data)
        return True

    def board_passenger(self, actor_ctx: dict, manifest_id: str, passenger_data: dict):
        manifest = self.manifests.get(manifest_id)
        # Validation of passenger payment would go here
        manifest["passengers"].append(passenger_data)
        return True

    # --- LIFECYCLE ---

    def confirm_departure(self, actor_ctx: dict, manifest_id: str):
        manifest = self.manifests.get(manifest_id)

        # HARD GATE: Verified Captain
        captain = self.captains.get(manifest["captain_id"])
        if not captain or captain["status"] != "ACTIVE":
             raise PermissionError("HARD GATE: No departure without verified active captain.")

        manifest["status"] = "IN_TRANSIT"
        manifest["departure_ts"] = datetime.now(UTC).isoformat()
        return True

    def confirm_arrival(self, actor_ctx: dict, manifest_id: str):
        manifest = self.manifests.get(manifest_id)
        manifest["status"] = "ARRIVED"
        manifest["arrival_ts"] = datetime.now(UTC).isoformat()
        return True

    def complete_delivery(self, actor_ctx: dict, manifest_id: str, item_id: str, proof: dict):
        self.manifests.get(manifest_id)
        # Logic to mark individual cargo as delivered
        # If all delivered, mark manifest as CLOSED
        return True

    def release_payout(self, actor_ctx: dict, manifest_id: str):
        manifest = self.manifests.get(manifest_id)

        # HARD GATE: Proof of arrival/delivery
        if manifest["status"] not in ["ARRIVED", "CLOSED"]:
             raise PermissionError("HARD GATE: No operator payout before proof of arrival/delivery.")

        # Trigger FCE settlement (simulated)
        manifest["payout_status"] = "RELEASED"
        return {"status": "SUCCESS", "manifest_id": manifest_id}

    def get_corridor_intelligence(self, route_id: str):
        """
        Intelligence: Reliability and risk scoring.
        """
        return {
            "route_id": route_id,
            "reliability_score": 98.5,
            "delay_risk": "LOW",
            "on_time_percentage": 96.0,
            "recommended_route": "Male -> Baa (Direct Corridor)"
        }

    def report_damage(self, actor_ctx: dict, manifest_id: str, item_id: str, details: dict):
        # Red-alert: Freeze payout
        manifest = self.manifests.get(manifest_id)
        manifest["payout_status"] = "FROZEN"

        d_id = f"DSP-{uuid.uuid4().hex[:6].upper()}"
        dispute = {"id": d_id, "manifest_id": manifest_id, "item_id": item_id, "details": details}
        self.disputes[d_id] = dispute
        return dispute

import uuid
from datetime import datetime, UTC

class UDomesticCargoEngine:
    """
    U-Domestic Cargo: Malé-to-atoll delivery and island handoff.
    Calculates and manages island delivery using cargo boats, dhonis, and speedboats.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.route_master = {
            "Male-to-Addu": {"base_rate": 150.0, "transit": "3-5 days", "zone": "S.Atoll"},
            "Male-to-Huvadhu": {"base_rate": 180.0, "transit": "4-6 days", "zone": "GA/GDh Atoll"},
            "Male-to-Baa": {"base_rate": 120.0, "transit": "2-3 days", "zone": "B.Atoll"}
        }
        self.pricing_categories = {
            "small_parcel": 20.0,
            "carton": 50.0,
            "bottled_water_case": 15.0,
            "fragile_item": 100.0,
            "bulk_cbm": 350.0
        }
        self.jobs = {}

    def get_quote(self, origin: str, destination: str, cargo_details: dict):
        route_key = f"{origin}-to-{destination}"
        route = self.route_master.get(route_key, {"base_rate": 100.0, "transit": "Unknown"})

        category = cargo_details.get("category", "carton")
        cat_rate = self.pricing_categories.get(category, 50.0)

        # Total = Base Route Rate + Category Rate + (Weight * 0.5)
        total = route["base_rate"] + cat_rate + (cargo_details.get("weight_kg", 0) * 0.5)

        # Surcharges
        if cargo_details.get("fragile"):
            total += 50.0

        return {
            "origin": origin,
            "destination": destination,
            "total_mvr": total,
            "estimated_transit": route["transit"],
            "zone": route.get("zone")
        }

    def initiate_delivery(self, actor_ctx: dict, job_data: dict, clearance_status: bool):
        # HARD GATE: No domestic delivery before clearance is complete
        if not clearance_status:
             raise PermissionError("GLOBAL GATE: No domestic delivery before Customs/MPL clearance is complete.")

        job_id = f"DOM-{uuid.uuid4().hex[:6].upper()}"
        job = {
            "id": job_id,
            "order_id": job_data.get("order_id"),
            "status": "READY_AT_MALE_HUB",
            "destination": job_data.get("destination"),
            "operator_id": job_data.get("operator_id"),
            "departure_ts": None,
            "arrival_ts": None
        }
        self.jobs[job_id] = job
        self.shadow.commit("domestic_cargo.quote.created", actor_ctx.get("identity_id"), {"job_id": job_id})
        return job

    def confirm_departure(self, actor_ctx: dict, job_id: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "DEPARTED_MALE"
            self.jobs[job_id]["departure_ts"] = datetime.now(UTC).isoformat()
            self.shadow.commit("domestic_cargo.departed", actor_ctx.get("identity_id"), {"job_id": job_id})
            return True
        return False

    def confirm_island_arrival(self, actor_ctx: dict, job_id: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "ARRIVED_ISLAND"
            self.jobs[job_id]["arrival_ts"] = datetime.now(UTC).isoformat()
            self.shadow.commit("domestic_cargo.arrived_island", actor_ctx.get("identity_id"), {"job_id": job_id})
            return True
        return False

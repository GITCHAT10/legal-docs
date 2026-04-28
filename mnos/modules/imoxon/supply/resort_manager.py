import uuid
import structlog
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, UTC

logger = structlog.get_logger("prestige.supply")

class ResortSupplyManager:
    """
    Prestige Supply Lock Layer: Manages Tier 1 & Tier 2 resorts.
    Targets 20 high-conversion resorts for Day 1 activation.
    """
    def __init__(self, core):
        self.core = core
        self.resorts = {} # resort_id -> metadata (rates, allotment, transfers)

    def onboard_resort(self, resort_data: dict):
        """Onboard a resort with net rates and transfer costs."""
        resort_id = resort_data.get("id")
        self.resorts[resort_id] = {
            "name": resort_data.get("name"),
            "tier": resort_data.get("tier"), # T1 (Cash Flow), T2 (Margin)
            "net_rates": resort_data.get("net_rates", {}), # room_type -> price
            "transfer_cost": Decimal(str(resort_data.get("transfer_cost", 0))),
            "allotment": resort_data.get("allotment", 0),
            "sla_hours": resort_data.get("sla_hours", 2),
            "status": "LIVE"
        }

        # Anchor in SHADOW
        self.core.execute_commerce_action(
            "supply.resort.onboarded",
            {"identity_id": "SYSTEM", "role": "admin", "device_id": "SYSTEM_VIRTUAL"},
            lambda: self.resorts[resort_id],
            resort_id
        )
        logger.info("resort_onboarded", resort_id=resort_id, tier=resort_data.get("tier"))

    def get_resort_offer(self, resort_id: str, room_type: str) -> Optional[dict]:
        resort = self.resorts.get(resort_id)
        if not resort or resort["status"] != "LIVE":
            return None

        net_rate = resort["net_rates"].get(room_type)
        if not net_rate:
            return None

        return {
            "resort_id": resort_id,
            "resort_name": resort["name"],
            "net_rate": Decimal(str(net_rate)),
            "transfer_cost": resort["transfer_cost"],
            "total_net": Decimal(str(net_rate)) + resort["transfer_cost"]
        }

    def batch_onboard_priority_20(self):
        """Day 1: Lock Supply for the top 20 high-conversion resorts."""
        priority_list = [
            # Tier 1 (Cash Flow)
            {"id": "KUREDU", "name": "Kuredu Island Resort", "tier": "T1", "transfer_cost": 350, "allotment": 15, "net_rates": {"GARDEN_VILLA": 250, "BEACH_VILLA": 450}},
            {"id": "VILAMENDHOO", "name": "Vilamendhoo Island Resort", "tier": "T1", "transfer_cost": 350, "allotment": 10, "net_rates": {"BEACH_VILLA": 480, "WATER_VILLA": 650}},
            {"id": "MEERU", "name": "Meeru Island Resort", "tier": "T1", "transfer_cost": 150, "allotment": 20, "net_rates": {"GARDEN_ROOM": 220, "BEACH_VILLA": 400}},
            {"id": "KURAMATHI", "name": "Kuramathi Maldives", "tier": "T1", "transfer_cost": 320, "allotment": 12, "net_rates": {"BEACH_VILLA": 500, "WATER_VILLA": 750}},
            {"id": "SUN_SIYAM_OLHUVELI", "name": "Sun Siyam Olhuveli", "tier": "T1", "transfer_cost": 210, "allotment": 18, "net_rates": {"GRAND_BEACH_VILLA": 420, "WATER_VILLA": 600}},

            # Tier 2 (Margin)
            {"id": "VELIGANDU", "name": "Veligandu Island Resort", "tier": "T2", "transfer_cost": 350, "allotment": 5, "net_rates": {"WATER_VILLA": 850, "BEACH_VILLA": 700}},
            {"id": "BAROS", "name": "Baros Maldives", "tier": "T2", "transfer_cost": 250, "allotment": 3, "net_rates": {"DELUXE_VILLA": 950, "BAROS_SUITE": 1800}},
            {"id": "MILAIDHOO", "name": "Milaidhoo Maldives", "tier": "T2", "transfer_cost": 600, "allotment": 2, "net_rates": {"WATER_POOL_VILLA": 1200}},
            {"id": "CHEVAL_BLANC", "name": "Cheval Blanc Randheli", "tier": "T2", "transfer_cost": 1200, "allotment": 1, "net_rates": {"WATER_VILLA": 3500}}
        ]

        for r in priority_list:
            self.onboard_resort(r)

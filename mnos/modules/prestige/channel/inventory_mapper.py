from typing import Dict, List, Optional
from pydantic import BaseModel
from enum import Enum

class InventoryStatus(str, Enum):
    LIVE_SELL = "LIVE_SELL"
    ON_REQUEST = "ON_REQUEST"
    HELD_FOR_AGENT = "HELD_FOR_AGENT"
    PENDING_SUPPLIER_CONFIRMATION = "PENDING_SUPPLIER_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    STOP_SELL = "STOP_SELL"
    WAITLIST = "WAITLIST"
    BLACKOUT = "BLACKOUT"

class InventoryItem(BaseModel):
    internal_id: str
    external_ids: Dict[str, str] = {} # channel_id -> ext_id
    supplier_id: str
    supplier_contract_ref: str
    inventory_type: str # hotel_room, villa, tour_package, etc.
    title: str
    description: str
    base_currency: str = "USD"
    base_price: float
    service_charge_rate: float = 0.10
    tgst_rate: float = 0.17
    green_tax_applicable: bool = True
    availability_window: Dict[str, str] # start_date, end_date
    cancellation_policy_ref: Optional[str] = None
    child_policy_ref: Optional[str] = None
    meal_plan: Optional[str] = None
    geo_constraints: List[str] = []
    transfer_requirements: bool = True
    privacy_level: int = 2
    status: InventoryStatus = InventoryStatus.ON_REQUEST

class InventoryMapper:
    def __init__(self, core_system):
        self.core = core_system
        self.inventory: Dict[str, InventoryItem] = {}

    def register_item(self, actor_ctx: dict, item: InventoryItem):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.register_inventory",
            actor_ctx,
            self._internal_register,
            item
        )

    def _internal_register(self, item: InventoryItem):
        # Validate through ORCA (mocked)
        if not self._validate_contract(item.supplier_contract_ref):
            raise ValueError(f"ORCA: Invalid supplier contract {item.supplier_contract_ref}")

        # Validate through FCE (mocked)
        if not self._validate_pricing(item):
            raise ValueError("FCE: Pricing validation failed")

        self.inventory[item.internal_id] = item

        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        self.core.shadow.commit("prestige.inventory.registered", actor_id, item.model_dump())
        return {"status": "success", "internal_id": item.internal_id}

    def _validate_contract(self, ref: str) -> bool:
        # Doctrine: validate supplier contract through ORCA
        if hasattr(self.core, "orca"):
            return self.core.orca.validate_contract(ref)
        return True # Simplified for pilot if ORCA not fully wired

    def _validate_pricing(self, item: InventoryItem) -> bool:
        # Doctrine: validate pricing through FCE
        if item.base_price <= 0:
            return False
        return True

    def get_item(self, internal_id: str) -> Optional[InventoryItem]:
        return self.inventory.get(internal_id)

    def get_by_external_id(self, channel_id: str, external_id: str) -> Optional[InventoryItem]:
        for item in self.inventory.values():
            if item.external_ids.get(channel_id) == external_id:
                return item
        return None

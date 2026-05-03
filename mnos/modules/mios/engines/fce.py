from uuid import UUID, uuid4
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
from mnos.modules.mios.schemas.models import FCELineItem

class MIOSFCEEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.ledger: Dict[UUID, List[FCELineItem]] = {}

    def add_line_item(self, actor_ctx: dict, shipment_id: UUID, category: str, name: str, amount_mvr: Decimal, verified: bool = False):
        item = FCELineItem(
            shipment_id=shipment_id,
            category=category,
            name=name,
            amount_mvr=amount_mvr,
            is_verified=verified
        )
        if shipment_id not in self.ledger:
            self.ledger[shipment_id] = []
        self.ledger[shipment_id].append(item)
        self.shadow.commit("mios.fce.line_added", actor_ctx["identity_id"], item.dict())

    def calculate_sky_clearance_sc(self, shipment_id: UUID) -> Decimal:
        # HYBRID_SC_V1: fixed_admin_fee + percentage_commission
        # fixed_admin_fee_mvr = 750
        # percentage_commission = 3%
        # minimum_sc_mvr = 750
        # cap_sc_mvr = 3500

        items = self.ledger.get(shipment_id, [])
        sc_base = sum(item.amount_mvr for item in items if item.category in [
            "CUSTOMS_CHARGES", "PORT_CHARGES", "BROKER_CHARGES", "TRANSPORT_CHARGES"
        ])

        commission = (sc_base * Decimal("0.03")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sc = Decimal("750") + commission

        sc = max(sc, Decimal("750"))
        sc = min(sc, Decimal("3500"))
        return sc

    def get_landed_cost(self, shipment_id: UUID) -> Decimal:
        items = self.ledger.get(shipment_id, [])
        return sum(item.amount_mvr for item in items)

    def lock_landed_cost(self, actor_ctx: dict, shipment_id: UUID):
        # Verification logic would go here (all receipts verified etc)
        self.shadow.commit("mios.fce.landed_cost_locked", actor_ctx["identity_id"], {"shipment_id": str(shipment_id)})

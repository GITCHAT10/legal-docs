from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime
from mnos.modules.mios.schemas.models import FXRate

class MIOSFXEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.rates: Dict[UUID, List[FXRate]] = {}

    def capture_rate(self, actor_ctx: dict, shipment_id: UUID, source: str, target: str, rate_type: str, rate: Decimal) -> FXRate:
        fx_rate = FXRate(
            shipment_id=shipment_id,
            source_currency=source,
            target_currency=target,
            rate_type=rate_type,
            rate=rate
        )
        if shipment_id not in self.rates:
            self.rates[shipment_id] = []
        self.rates[shipment_id].append(fx_rate)
        self.shadow.commit("mios.fx.rate_captured", actor_ctx["identity_id"], fx_rate.dict())
        return fx_rate

    def lock_rate(self, actor_ctx: dict, shipment_id: UUID, rate_type: str):
        shipment_rates = self.rates.get(shipment_id, [])
        for r in shipment_rates:
            if r.rate_type == rate_type:
                r.is_locked = True
                self.shadow.commit("mios.fx.rate_locked", actor_ctx["identity_id"], {"shipment_id": str(shipment_id), "rate_type": rate_type})
                return
        raise ValueError(f"Rate type {rate_type} not found for shipment {shipment_id}")

    def calculate_variance(self, shipment_id: UUID, rate_type_a: str, rate_type_b: str) -> Decimal:
        shipment_rates = self.rates.get(shipment_id, [])
        rate_a = next((r.rate for r in shipment_rates if r.rate_type == rate_type_a), None)
        rate_b = next((r.rate for r in shipment_rates if r.rate_type == rate_type_b), None)

        if rate_a is None or rate_b is None:
            return Decimal("0")

        return rate_b - rate_a

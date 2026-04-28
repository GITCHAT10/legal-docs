from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from .inventory import AllotmentEngine

class SupplyRequest(BaseModel):
    product_type: str  # accommodation | transfer | activity
    dates: List[date]
    units: int
    segment: Optional[str] = "default"

class SupplyResponse(BaseModel):
    contract_id: str
    net_amount: Decimal = Field(gt=0)
    product_type: str
    tax_type: str
    availability_pct: float
    trigger_hint: str  # "urgency" | "volume" | "stable"

class SupplyRouter:
    def __init__(self, allotment_engine: AllotmentEngine):
        self.engine = allotment_engine

    async def resolve(self, req: SupplyRequest) -> SupplyResponse:
        # 1. Fetch active contract for product/date range
        # (Simplified: assumes 1:1 mapping. In prod: join with rate_plans)
        contract_id = self._lookup_contract(req)

        # 2. Calculate availability %
        remaining = await self._get_remaining_units(contract_id, req.dates)
        total = await self._get_total_units(contract_id, req.dates)
        avail_pct = (remaining / total) * 100 if total > 0 else 0.0

        # 3. Trigger hint logic
        if avail_pct < 20:
            hint = "urgency"
        elif avail_pct > 60:
            hint = "volume"
        else:
            hint = "stable"

        # 4. Return pricing-ready payload
        return SupplyResponse(
            contract_id=contract_id,
            net_amount=self._get_base_rate(contract_id),
            product_type=req.product_type,
            tax_type="TOURISM" if req.product_type != "retail" else "RETAIL",
            availability_pct=round(avail_pct, 2),
            trigger_hint=hint
        )

    # Placeholder stubs (replace with DB queries)
    def _lookup_contract(self, req: SupplyRequest) -> str: return "contract_01"
    async def _get_remaining_units(self, cid, dates) -> int: return 8
    async def _get_total_units(self, cid, dates) -> int: return 10
    def _get_base_rate(self, cid) -> Decimal: return Decimal("145.00")

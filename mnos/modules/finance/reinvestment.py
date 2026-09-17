import uuid
from datetime import datetime, UTC
from decimal import Decimal, ROUND_HALF_UP

class RevenueReinvestmentEngine:
    """
    REVENUE-REINVESTMENT-ENGINE: Sovereign Economic Feedback Loop.
    Allocates a percentage of island tax revenue back to local infrastructure funds.
    Formula: ISLAND_RETURN = (TGST + Green Tax) * 0.25
    Tiers: Direct Island Fund (Jetty/Waste), Shared Atoll Infra, National Reserve.
    """
    def __init__(self, core):
        self.core = core
        self.island_funds = {} # island -> {total_allocated, tiers: {T1, T2, T3}}
        self.allocation_history = []
        self.reinvestment_rate = Decimal("0.25") # 25%

    def process_island_reinvestment(self, island: str, tgst: float, green_tax: float):
        """MIRA Integration: Auto-calculate and lock allocation."""
        total_tax = Decimal(str(tgst)) + Decimal(str(green_tax))
        allocated_amount = (total_tax * self.reinvestment_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if island not in self.island_funds:
            self.island_funds[island] = {
                "total_allocated": 0.0,
                "tiers": {"T1": 0.0, "T2": 0.0, "T3": 0.0},
                "status": "OPERATIONAL"
            }

        fund = self.island_funds[island]

        # Tiered Distribution: 50% T1, 30% T2, 20% T3
        t1 = (allocated_amount * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        t2 = (allocated_amount * Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        t3 = allocated_amount - t1 - t2

        fund["total_allocated"] += float(allocated_amount)
        fund["tiers"]["T1"] += float(t1)
        fund["tiers"]["T2"] += float(t2)
        fund["tiers"]["T3"] += float(t3)

        allocation_event = {
            "id": f"REINV-{uuid.uuid4().hex[:6].upper()}",
            "island": island,
            "amount": float(allocated_amount),
            "breakdown": {"T1": float(t1), "T2": float(t2), "T3": float(t3)},
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.allocation_history.append(allocation_event)

        # SHADOW ENFORCEMENT: CALCULATED -> APPROVED -> LOCKED -> LOGGED
        self.core.shadow.commit("finance.reinvestment.allocated", island, allocation_event)

        return allocation_event

    def get_island_fund_status(self, island: str):
        return self.island_funds.get(island, {"total_allocated": 0, "status": "INACTIVE"})

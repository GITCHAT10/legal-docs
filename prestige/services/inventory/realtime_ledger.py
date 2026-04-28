import asyncio
from datetime import datetime, UTC
import structlog

logger = structlog.get_logger("inventory.ledger")

class RealtimeInventoryLedger:
    """
    Unified inventory ledger with supplier webhooks.
    Prevents overbooking across resorts, jets, yachts, transfers.
    """
    def __init__(self, core):
        self.core = core
        self.inventory = {} # (product_code, date) -> available_slots
        self.holds = {} # booking_id -> list of (product_code, date, slots)

    async def sync_supplier_inventory(self, supplier_id: str, items: list):
        """Ingest supplier availability."""
        for item in items:
            key = (item['product_code'], item['date'])
            self.inventory[key] = int(item['available_slots'])

            # Emit inventory event for OODA consumption
            self.core.events.publish("prestige.inventory.updated", {
                "product_code": item['product_code'],
                "date": item['date'],
                "available_slots": self.inventory[key],
                "supplier_id": supplier_id,
                "timestamp": datetime.now(UTC).isoformat()
            })

    async def hold_inventory(self, product_code: str, date: str, slots: int, booking_id: str) -> bool:
        """Distributed lock (simulated) for 5-min hold during booking flow."""
        key = (product_code, date)
        if self.inventory.get(key, 0) < slots:
            return False

        self.inventory[key] -= slots
        if booking_id not in self.holds:
            self.holds[booking_id] = []
        self.holds[booking_id].append((product_code, date, slots))
        return True

    async def confirm_or_release(self, booking_id: str, confirmed: bool):
        """Convert hold -> sale, or release back to pool."""
        holds = self.holds.pop(booking_id, [])
        if not confirmed:
            for product_code, date, slots in holds:
                key = (product_code, date)
                self.inventory[key] += slots
        return True

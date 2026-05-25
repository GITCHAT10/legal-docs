from fastapi import APIRouter, Depends
from typing import Dict, List

def create_orca_router(hospitality, bpe, shadow_core, get_actor_ctx):
    router = APIRouter(tags=["orca"])

    @router.get("/dashboard/summary")
    async def get_summary(actor: dict = Depends(get_actor_ctx)):
        """ORCA: Minimum Running Stack Dashboard."""

        # 1. Total Bookings (HOSPITALITY)
        total_bookings = len(hospitality.bookings)

        # 2. Total Revenue (Calculated from SHADOW committed invoices)
        revenue_mvr = 0.0
        for block in shadow_core.chain:
            payload = block.get("payload", {})

            # Check for completed transactions from Guard
            result = payload.get("result")
            if isinstance(result, dict):
                # Search for pricing in results (e.g. from hospitality.book_stay)
                if "pricing" in result:
                    revenue_mvr += result["pricing"].get("total", 0.0)

            # Also check for bpe offline sync pricing
            if "offline_sync" in block.get("event_type", ""):
                 pricing = payload.get("pricing")
                 if pricing and isinstance(pricing, dict):
                    revenue_mvr += pricing.get("total", 0.0)

        # 3. Pending Sync Items
        sync_items = [b for b in shadow_core.chain if "offline_sync" in b.get("event_type", "")]

        # 4. Audit Status
        audit_ok = shadow_core.verify_integrity()

        return {
            "node_id": "SALA-EDGE-01",
            "metrics": {
                "total_bookings_today": total_bookings,
                "total_revenue_mvr": round(revenue_mvr, 2),
                "synced_offline_records": len(sync_items),
                "audit_status": "OK" if audit_ok else "ALERT"
            },
            "status": "OPERATIONAL"
        }

    return router

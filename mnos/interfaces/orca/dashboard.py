import json
import os

class OrcaDashboard:
    def __init__(self, shadow, wallet):
        self.shadow = shadow
        self.wallet = wallet

    def get_live_metrics(self):
        chain = self.shadow.chain
        total_revenue = 0
        order_count = 0
        for block in chain:
            if block.get("event_type") == "upos.order.completed":
                order_count += 1
                # Standardized safe dictionary access to prevent KeyError (Offline-First resilience)
                payload = block.get("payload", {})
                pricing = payload.get("pricing")

                if pricing and isinstance(pricing, dict):
                    total_revenue += pricing.get("total", 0)
                elif "amount" in payload:
                    # Fallback for events that have amount but weren't enriched yet (should not happen in completed)
                    total_revenue += payload.get("amount", 0)
                else:
                    # Log anomaly for SHADOW audit (Simulated via print or internal log)
                    print(f"[ANOMALY] Missing pricing in SHADOW block {block.get('index')}")

        # P&L Simulation
        payouts = 0
        fees = 0
        if self.wallet and hasattr(self.wallet, "settlements"):
            payouts = sum(s.get("net_amount", 0) for s in self.wallet.settlements.values())
            fees = sum(s.get("platform_fee", 0) for s in self.wallet.settlements.values())

        return {
            "node_status": "ACTIVE",
            "total_revenue_mvr": total_revenue,
            "order_count": order_count,
            "total_payouts_mvr": payouts,
            "platform_fees_mvr": fees,
            "audit_integrity": self.shadow.verify_integrity(),
            "sync_status": "STABLE"
        }

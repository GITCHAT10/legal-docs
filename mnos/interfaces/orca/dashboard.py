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
            if block["event_type"] == "upos.order.completed":
                order_count += 1
                # Standardized safe dictionary access to prevent KeyError
                total_revenue += block.get("payload", {}).get("pricing", {}).get("total", 0)

        # P&L Simulation
        payouts = sum(s["net_amount"] for s in self.wallet.settlements.values())
        fees = sum(s["platform_fee"] for s in self.wallet.settlements.values())

        return {
            "node_status": "ACTIVE",
            "total_revenue_mvr": total_revenue,
            "order_count": order_count,
            "total_payouts_mvr": payouts,
            "platform_fees_mvr": fees,
            "audit_integrity": self.shadow.verify_integrity(),
            "sync_status": "STABLE"
        }

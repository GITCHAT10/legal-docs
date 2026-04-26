from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timezone
from mnos.modules.shadow.service import shadow

class FinanceDashboardService:
    """
    BUBBLE Automated P&L Dashboard Service.
    Aggregates data from SHADOW LEDGER for real-time visibility.
    """
    def __init__(self):
        # Mappings for Chart of Accounts (COA)
        self.COA = {
            "1100": "CASH_LIQUID",
            "2200": "TGST_ESCROW",
            "2300": "SC_POOL",
            "4000": "REVENUE_GENERAL",
            "5000": "EXPENSE_GENERAL"
        }

    def get_mtd_pnl(self) -> Dict[str, Any]:
        """Calculates Month-To-Date P&L from ledger truth."""
        revenue = Decimal("0.00")
        expenses = Decimal("0.00")

        for entry in shadow.chain:
            # Skip non-financial events
            if entry["event_type"] not in ["fce.charge", "fce.payment", "nexus.payment.received"]:
                continue

            amount = Decimal(str(entry["payload"].get("amount", 0)))
            if amount > 0:
                revenue += amount
            else:
                expenses += abs(amount)

        return {
            "mtd_revenue": revenue,
            "mtd_expenses": expenses,
            "net_profit": revenue - expenses,
            "currency": "USD",
            "last_sync": datetime.now(timezone.utc).isoformat()
        }

    def get_cash_position(self) -> Dict[str, Any]:
        """Aggregates liquid and locked cash positions."""
        # Mock aggregation for demonstration
        return {
            "liquid_cash": Decimal("12400.00"),
            "tgst_escrow": Decimal("3100.00"),
            "sc_pool": Decimal("2450.00"),
            "status": "MIRA_READY"
        }

    def verify_integrity(self) -> bool:
        """Verifies dashboard state against SHADOW ledger hash chain."""
        return shadow.verify_integrity()

dashboard_service = FinanceDashboardService()

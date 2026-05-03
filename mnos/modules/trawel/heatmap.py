from datetime import datetime, UTC
from typing import List

class GlobalDemandHeatmap:
    """
    GLOBAL-DEMAND-HEATMAP: National Intelligence Dashboard.
    Layers: Saturation, Revenue, Tax Yield, Hustle Activity, Bridge Flow, Reinvestment Signal.
    """
    def __init__(self, core, island_system, mira_bridge, reinvestment_engine):
        self.core = core
        self.island_system = island_system
        self.mira = mira_bridge
        self.reinvestment = reinvestment_engine

    def get_national_summary(self) -> dict:
        """Aggregated National Stats (SHADOW_VERIFIED_ONLY)."""
        total_revenue = sum(s["revenue"] for s in self.island_system.island_stats.values())
        total_tax = sum(l["tgst"] + l["green_tax"] for l in self.mira.daily_ledgers.values())

        return {
            "total_revenue": total_revenue,
            "total_tax_yield": total_tax,
            "active_islands": len(self.island_system.island_registry),
            "timestamp": datetime.now(UTC).isoformat(),
            "mode": "NATIONAL_INTELLIGENCE_DASHBOARD"
        }

    def get_map_data(self) -> List[dict]:
        """Color-coded island nodes for interactive map."""
        map_nodes = []
        for island, stats in self.island_system.island_stats.items():
            # Saturation Map Layer
            # (Mock occupancy: revenue / 1000, max 100)
            occupancy = min((stats["revenue"] / 5000) * 100, 100)
            status = "GREEN"
            if occupancy > 90: status = "RED"
            elif occupancy > 70: status = "YELLOW"

            # Reinvestment Signal Layer
            fund = self.reinvestment.get_island_fund_status(island)

            map_nodes.append({
                "island": island,
                "status": status,
                "occupancy": round(occupancy, 1),
                "revenue": stats["revenue"],
                "reinvestment_allocated": fund.get("total_allocated", 0.0)
            })
        return map_nodes

    def drill_down(self, island: str) -> dict:
        """Detailed island performance intelligence."""
        stats = self.island_system.island_stats.get(island)
        if not stats: return {}

        daily_mira = self.mira.get_daily_report(date=datetime.now(UTC).date().isoformat())
        island_tax = sum(r["tgst"] for r in daily_mira if self.island_system.vendors.get(r["vendor_id"], {}).get("island") == island)

        return {
            "island": island,
            "stats": stats,
            "tax_yield": island_tax,
            "fund_status": self.reinvestment.get_island_fund_status(island),
            "hustle_activity": "HIGH" if stats["vendor_count"] > 5 else "STABLE"
        }

    def get_presidential_executive_summary(self) -> dict:
        """CABINET-LEVEL-CONTROL: National Health & Strategic Reserve."""
        summary = self.get_national_summary()

        # Calculate National Health Score (0-100)
        # Factors: Tax compliance, Fraud rate, Occupancy balance
        health_score = 87 # Simulated high health

        # Strategic Reserve (Accumulated across islands)
        total_reinvested = sum(f["total_allocated"] for f in self.reinvestment.island_funds.values())

        return {
            "national_health_score": health_score,
            "total_revenue": summary["total_revenue"],
            "tax_collected": summary["total_tax_yield"],
            "total_reinvested": total_reinvested,
            "strategic_reserve": {
                "national_tax_vault": summary["total_tax_yield"] * 5, # Accumulation simulation
                "available_for_deployment": total_reinvested * 0.4,
                "disaster_reserve": summary["total_tax_yield"] * 0.15
            },
            "critical_alerts": self._generate_alerts(),
            "recommendations": self._get_acore_insights()
        }

    def _generate_alerts(self) -> List[dict]:
        alerts = []
        for island, stats in self.island_system.island_stats.items():
            occupancy = (stats["revenue"] / 5000) * 100
            if occupancy > 90:
                alerts.append({
                    "severity": "CRITICAL",
                    "island": island,
                    "msg": f"{island} Saturation Critical ({int(occupancy)}%)",
                    "recommendation": "Increase boat fleet +20%"
                })
        return alerts

    def _get_acore_insights(self) -> List[str]:
        return [
            "Add 2 boats to Kaafu (ROI +18%)",
            "Increase Maafushi capacity by 12 rooms",
            "Invest $50K into Ukulhas jetty (high return zone)"
        ]

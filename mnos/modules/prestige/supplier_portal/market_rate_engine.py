from typing import List
from mnos.modules.prestige.supplier_portal.models import MarketSellingRate, CMOMarketStrategyProfile

class MarketRateEngine:
    """
    Generates market-specific selling rates.
    Rules: respect margin floor, do not alter FCE tax logic, distribute only sealed rates.
    """
    def generate_market_rates(self, net_rate: float, category: str, strategy: CMOMarketStrategyProfile) -> List[MarketSellingRate]:
        regions = ["EU", "CIS", "GCC", "Asia", "India", "China", "Global_UHNW"]
        rates = []

        for region in regions:
            markup_attr = f"{region}_markup_percent"
            markup_pct = getattr(strategy, markup_attr, 15.0) / 100.0

            # Base Selling = Net + (Net * Markup)
            base_selling = net_rate * (1 + markup_pct)

            # 1. 10% Service Charge
            sc = base_selling * 0.10
            subtotal = base_selling + sc

            # 2. 17% TGST
            tgst = subtotal * 0.17

            final_rate = subtotal + tgst

            rates.append(MarketSellingRate(
                market_region=region,
                category_code=category,
                selling_rate=round(final_rate, 2),
                tax_breakdown={
                    "service_charge": round(sc, 2),
                    "tgst": round(tgst, 2)
                },
                margin_amount=round(base_selling - net_rate, 2),
                commission_amount=round(base_selling * (strategy.agent_commission_percent / 100.0), 2),
                safe_to_publish=False # Requires final FCE/SHADOW gates
            ))

        return rates

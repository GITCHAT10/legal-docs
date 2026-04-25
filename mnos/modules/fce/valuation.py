from typing import Dict, Any
from decimal import Decimal
from mnos.modules.fce.fx_service import fx_authority
from mnos.shared import constants

class FCEValuation:
    """
    FCE Valuation & FX Lock:
    Implements dual-currency capture at financial intent.
    """
    def capture_intent(self, amount: Decimal, region_code: str) -> Dict[str, Any]:
        """
        Captures financial intent with FX lock and dual-currency fields.
        """
        region = constants.REGIONS.get(region_code)
        if not region:
            raise ValueError(f"FCE_VALUATION: Unknown region {region_code}")

        currency_local = region['currency']
        rate_info = fx_authority.fetch_fx_rate(currency_local, 'USD')

        fx_rate = rate_info['value']
        amount_usd = (amount * fx_rate).quantize(Decimal('0.01'))

        financial_intent = {
            "amount_local": amount,
            "currency_local": currency_local,
            "fx_rate_to_usd": fx_rate,
            "fx_timestamp": rate_info['timestamp'],
            "fx_source": rate_info['source'],
            "fx_provider": rate_info['provider'],
            "amount_usd": amount_usd,
            "reporting_currency": 'USD'
        }

        print(f"[VALUATION] Financial Intent Captured: {amount} {currency_local} -> {amount_usd} USD")
        return financial_intent

valuation_engine = FCEValuation()

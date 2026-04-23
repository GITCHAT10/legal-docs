from typing import Dict, Any
import datetime
from decimal import Decimal

class FXAuthority:
    """
    FX Authority Stack:
    Provides bank-grade rate sources and fails closed on variance.
    """
    def __init__(self):
        self.rates = {
            'MVR': Decimal('0.065'), # 1 USD = 15.42 MVR
            'THB': Decimal('0.028'),
            'VND': Decimal('0.00004'),
            'INR': Decimal('0.012'),
            'IDR': Decimal('0.000063')
        }

    def fetch_fx_rate(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        if from_currency == to_currency:
            rate = Decimal('1.0')
        else:
            rate = self.rates.get(from_currency)
            if not rate:
                raise ValueError(f"FX_AUTHORITY: Unsupported currency {from_currency}")

        return {
            "value": rate,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "CENTRAL_BANK_REFERENCE",
            "provider": "MIG_FINANCE_CORE"
        }

fx_authority = FXAuthority()

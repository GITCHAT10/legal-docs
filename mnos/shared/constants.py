# MIG DUAL-REPORTING STANDARD: Constants
# Local legal truth + USD investor truth

ROOT_IDENTITY = 'MIG SOVEREIGN INFRASTRUCTURE'
SOVEREIGN_REPORTING_CURRENCY = 'USD'
CURRENCY_DENOMINATOR = 'USD'
LOCAL_PAYMENT_MANDATE = True
LOCAL_MANDATE = True
DUAL_CURRENCY_REQUIRED = True
FX_LOCK_AT_INTENT = True
NO_POST_EVENT_RECALCULATION = True

# Regional Jurisdictions
REGIONS = {
    'MV': {'currency': 'MVR', 'tax_engine': 'MV_MIRA'},
    'TH': {'currency': 'THB', 'tax_engine': 'TH_RD'},
    'VN': {'currency': 'VND', 'tax_engine': 'VN_TAX'},
    'IN': {'currency': 'INR', 'tax_engine': 'IN_GST'},
    'ID': {'currency': 'IDR', 'tax_engine': 'ID_BKPM'}
}

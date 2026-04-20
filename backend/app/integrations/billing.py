class BillingAdapter:
    """
    Bucket B: Output Billing/Offset API.
    Pushes Carbon Surcharge back to guest folios.
    """
    def post_surcharge(self, guest_id: str, amount_usd: float):
        # API call to PMS Folio system
        return True

    def execute_offset_trade(self, tonnage: float):
        # Transaction via carbon marketplaces
        return "TX-HASH-12345"

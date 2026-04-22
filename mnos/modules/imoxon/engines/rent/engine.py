class RentEngine:
    """
    IMOXON HOMES: Property and tenancy management.
    Compliant with Maldives Tenancy Act 2021.
    """
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.tenancies = {}

    def create_tenancy(self, landlord_id: str, tenant_id: str, property_id: str, monthly_rent: float, deposit: float):
        # 1. Validation (Tenancy Act: Deposit check)
        if deposit > (monthly_rent * 2):
            raise ValueError("AEGIS.POLICY: Security deposit cannot exceed 2 months rent.")

        tenancy_id = f"ten_{hash(landlord_id + tenant_id + property_id) % 10000}"
        tenancy = {
            "id": tenancy_id,
            "landlord": landlord_id,
            "tenant": tenant_id,
            "property": property_id,
            "monthly_rent": monthly_rent,
            "deposit": deposit,
            "status": "ACTIVE",
            "overdue_count": 0
        }

        # 2. Commit & Record
        self.shadow.record_action("homes.tenancy_created", tenancy)
        self.tenancies[tenancy_id] = tenancy

        # 3. Trigger events
        self.events.trigger("RENT_BILL_CREATED", {"tenancy_id": tenancy_id, "amount": monthly_rent})
        return tenancy

    def record_rent_payment(self, tenancy_id: str, amount: float):
        # Pricing via FCE
        pricing = self.fce.price_order(amount)
        payment = {
            "tenancy_id": tenancy_id,
            "amount": amount,
            "pricing": pricing,
            "status": "PAID",
            "timestamp": "now"
        }
        self.shadow.record_action("homes.rent_paid", payment)
        self.events.trigger("RENT_PAID", payment)
        return payment

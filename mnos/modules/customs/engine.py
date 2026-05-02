
class UCustomsEngine:
    """
    U-Customs: HS code lookup and landed cost estimation.
    Ingests National Tariff Schedule 2026.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        # National Tariff Schedule 2026 (Sample representation)
        self.tariff_schedule = {
            "6302.6000": {
                "desc": "Toilet linen and kitchen linen, of terry towelling",
                "unit": "kg",
                "mfn_rate": 0.20,
                "safta_rate": 0.05,
                "cmfta_rate_2026": 0.00
            },
            "8504.4000": {
                "desc": "Static converters (e.g. phone chargers)",
                "unit": "u",
                "mfn_rate": 0.05,
                "safta_rate": 0.00,
                "cmfta_rate_2026": 0.00
            },
            "9403.6000": {
                "desc": "Other wooden furniture",
                "unit": "u",
                "mfn_rate": 0.15,
                "safta_rate": 0.00,
                "cmfta_rate_2026": 0.00
            }
        }

    def lookup_hs_code(self, national_hs_code: str):
        return self.tariff_schedule.get(national_hs_code)

    def calculate_landed_cost(self, product: dict, freight: float):
        base_value = product.get("base_price", 0)
        # CIF = Cost + Insurance + Freight
        # Standard insurance estimate: 1% of cost
        insurance = base_value * 0.01
        cif_value = base_value + freight + insurance

        # Duty calculation
        hs_code = product.get("hs_code", "6302.6000")
        tariff = self.lookup_hs_code(hs_code) or {"mfn_rate": 0.15}
        rate = tariff.get("mfn_rate", 0.15)
        duty = cif_value * rate

        # Import GST (currently 8% in Maldives for imports)
        # Note: GST is calculated on (CIF + Duty)
        import_gst = (cif_value + duty) * 0.08

        # Processing and administrative fees
        processing_fee = 100.0 # Standard fee

        customs_reserve = duty + import_gst + processing_fee + 50.0 # with 50 MVR buffer

        return {
            "cif_value": cif_value,
            "duty_estimate": duty,
            "import_gst_estimate": import_gst,
            "processing_fee": processing_fee,
            "customs_reserve": customs_reserve,
            "hs_code": hs_code,
            "rate_applied": rate
        }

    def create_declaration(self, actor_ctx: dict, shipment_id: str, documents: list):
        # Mandatory document check
        required = ["commercial_invoice", "packing_list", "bill_of_lading"]
        for doc in required:
            if doc not in documents:
                 raise ValueError(f"Missing mandatory document: {doc}")

        return {"status": "DECLARED", "shipment_id": shipment_id}

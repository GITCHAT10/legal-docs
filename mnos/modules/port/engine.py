
class UPortEngine:
    """
    U-Port Charges: MPL tariff estimation based on Version V.02.2026.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        # MPL Tariffs 2026 (Sample representation)
        self.tariffs = {
            "LCL": {
                "handling": 25.0,
                "wharfage": 10.0,
                "stevedoring": 15.0,
                "unit": "Freight Tonne (max of CBM or MT)"
            },
            "20FT": {
                "handling": 2500.0,
                "wharfage": 500.0,
                "stevedoring": 1200.0,
                "unit": "Per Container"
            },
            "40FT": {
                "handling": 4500.0,
                "wharfage": 800.0,
                "stevedoring": 2000.0,
                "unit": "Per Container"
            }
        }

    def calculate_charges(self, cargo_data: dict):
        """
        Calculates port charges based on MPL 2026 schedule.
        """
        ctype = cargo_data.get("cargo_type", "LCL")
        tariff = self.tariffs.get(ctype, self.tariffs["LCL"])

        # Cargo measurement logic: max(metric_tonne, cbm)
        weight_mt = cargo_data.get("weight_kg", 0) / 1000.0
        cbm = cargo_data.get("cbm", 0)
        freight_tonne = max(weight_mt, cbm)

        multiplier = 1.0
        if ctype == "LCL":
             multiplier = freight_tonne
             if multiplier < 1.0:
                multiplier = 1.0

        base_handling = tariff["handling"] * multiplier
        base_wharfage = tariff["wharfage"] * multiplier
        base_stevedoring = tariff["stevedoring"] * multiplier

        base_total = base_handling + base_wharfage + base_stevedoring
        gst = base_total * 0.08

        return {
            "charge_details": tariff,
            "base_total": base_total,
            "gst": gst,
            "total_gst_inclusive": base_total + gst,
            "freight_tonne": freight_tonne,
            "port_storage_reserve": 500.0 # Default reserve for potential storage fees
        }

    def record_payment(self, actor_ctx: dict, invoice_id: str, amount: float):
        return True

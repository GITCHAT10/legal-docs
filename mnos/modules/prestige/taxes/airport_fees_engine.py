import json
import os
from decimal import Decimal
from typing import Dict, List, Any, Optional
from mnos.modules.prestige.taxes.airport_fees_schema import AirportFeeRule, FeeCode, PassengerResidency, TravelClass

class AirportFeesEngine:
    def __init__(self, table_path: str = None):
        if not table_path:
            # Default path relative to this file
            table_path = os.path.join(os.path.dirname(__file__), "airport_fees_table.json")

        with open(table_path, "r") as f:
            data = json.load(f)
            self.rules = [AirportFeeRule(**r) for r in data]

    def calculate_airport_fees(
        self,
        travel_class: TravelClass,
        residency: PassengerResidency,
        departure_airport: str,
        is_infant: bool = False,
        is_diplomat: bool = False,
        is_transit: bool = False,
        is_direct_transit: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates DPT and ADF based on statutory rules.
        Fail closed if required parameters are missing.
        """
        if not travel_class or not residency or not departure_airport:
             raise ValueError("FAIL CLOSED: travel_class, residency, and departure_airport are required.")

        fees = []
        total_amount = Decimal("0.00")

        for rule in self.rules:
            if rule.status != "active":
                continue

            # Check Residency Match
            if rule.passenger_residency != PassengerResidency.ANY and rule.passenger_residency != residency:
                continue

            # Check Travel Class Match
            if rule.travel_class != travel_class:
                continue

            # Check Airport Match (ADF specific)
            if rule.applies_to_airport and rule.applies_to_airport != departure_airport:
                continue

            # Apply Exemptions
            exempt = False
            if rule.fee_code == FeeCode.DPT:
                if is_infant and rule.exemption_rule.get("infant_under_2"): exempt = True
                if is_diplomat and rule.exemption_rule.get("diplomatic"): exempt = True
                if is_transit and rule.exemption_rule.get("transit"): exempt = True

            if rule.fee_code == FeeCode.ADF:
                if is_diplomat and rule.exemption_rule.get("diplomatic"): exempt = True
                if is_direct_transit and rule.exemption_rule.get("direct_transit"): exempt = True

            if not exempt:
                fees.append({
                    "code": rule.fee_code.value,
                    "name": rule.fee_name,
                    "amount": float(rule.amount_usd)
                })
                total_amount += rule.amount_usd

        return {
            "total_airport_fees_usd": float(total_amount),
            "breakdown": fees,
            "departure_airport": departure_airport,
            "travel_class": travel_class.value,
            "residency": residency.value,
            "is_statutory_pass_through": True,
            "is_prestige_margin": False
        }

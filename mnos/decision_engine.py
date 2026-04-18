class AegisPolicyEngine:
    @staticmethod
    def validate_request(fuel_request: dict):
        flight_id = fuel_request.get("flight_id", "")
        aircraft_id = fuel_request.get("aircraft_id", "")

        # Policy: flight_id must start with 'FL' and aircraft_id must start with 'AC'
        if not flight_id.startswith("FL"):
            return False, "Invalid flight ID"
        if not aircraft_id.startswith("AC"):
            return False, "Invalid aircraft ID"

        return True, "Policy check passed"

class FinancialControlEngine:
    @staticmethod
    def check_clearance(fuel_request: dict):
        amount = fuel_request.get("fuel_amount", 0)
        operator_id = fuel_request.get("operator_id", "")

        # Financial: operators starting with 'BLACKLIST' are denied
        if operator_id.startswith("BLACKLIST"):
            return False, "Operator blacklisted"

        # For simulation: amount > 1000 requires special credit (which we simulate as DENY for now)
        if amount > 1000:
            return False, "Insufficient credit for large amount"

        return True, "Financial clearance granted"

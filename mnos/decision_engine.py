from unified_suite.core.patente import NexGenPatenteVerifier
import logging

logger = logging.getLogger("unified_suite")

class AegisPolicyEngine:
    @staticmethod
    def validate_request(fuel_request: dict):
        flight_id = fuel_request.get("flight_id", "")
        aircraft_id = fuel_request.get("aircraft_id", "")

        # Sovereign Requirement: Unified PATENTE Validation
        operator_id = fuel_request.get("operator_id", "")
        patente_token = fuel_request.get("signature", "") # Reusing signature field for patente in this sim context

        # DEBUG
        # import os
        # logger.info(f"DEBUG: operator_id={operator_id}, token={patente_token}, hash_env={os.getenv('PATENTE_HASH')}")

        # For simulation simplicity, we will skip area validation if operator starts with CAPT
        # But token validation is mandatory
        try:
            # Check if PATENTE_HASH matches token hash
            import os
            import hashlib
            expected = os.getenv("PATENTE_HASH")
            if not expected or hashlib.sha256(patente_token.encode()).hexdigest() != expected:
                 return False, "PATENTE validation failed"
        except:
             return False, "PATENTE validation failed"

        # Sovereign Requirement: Asset Validation
        # In a real system, we would query the unified_suite service
        # Here we simulate: Aircrafts with 'UNKNOWN' in ID are rejected
        if "UNKNOWN" in aircraft_id:
            return False, "Unrecognized Asset: Aircraft not registered"

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

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
            if not NexGenPatenteVerifier.authorize_access(patente_token, operator_id, "FUEL_ACCESS"):
                 return False, "PATENTE validation failed or insufficient scope"
        except Exception as e:
             logger.error(f"PATENTE Error in Decision Engine: {str(e)}")
             return False, f"PATENTE error: {str(e)}"

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
    # Track fuel allocation to prevent over-fueling
    _fuel_ledger = {}

    @classmethod
    def check_clearance(cls, fuel_request: dict):
        amount = fuel_request.get("fuel_amount", 0)
        operator_id = fuel_request.get("operator_id", "")

        # Financial: operators starting with 'BLACKLIST' are denied
        if operator_id.startswith("BLACKLIST"):
            return False, "Operator blacklisted"

        # For simulation: amount > 1000 requires special credit (which we simulate as DENY for now)
        if amount > 1000:
            return False, "Insufficient credit for large amount"

        # CONCURRENCY & LIMIT CHECK
        aircraft_id = fuel_request.get("aircraft_id", "UNKNOWN")
        current_total = cls._fuel_ledger.get(aircraft_id, 0)
        if current_total + amount > 5000:
            return False, f"Daily limit exceeded for {aircraft_id}. Already fueled {current_total}L"

        cls._fuel_ledger[aircraft_id] = current_total + amount
        return True, "Financial clearance granted"

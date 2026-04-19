import hashlib
import hmac
import os
import logging

logger = logging.getLogger("unified_suite")

def authorize_access(token: str, entity_id: str, required_scope: str):
    """
    PRODUCTION-LOCKED AUTHORIZATION (MNOS-COMPLIANT)
    Enforces SHA256 token validation and Scope-Based Access Control (SBAC).
    """
    if not token:
        logger.error(f"Sovereign Auth Failure: Missing token for {entity_id}")
        raise PermissionError("Missing patente token")

    expected_hash = os.getenv("PATENTE_HASH")
    if not expected_hash:
        logger.critical("Sovereign Configuration Error: PATENTE_HASH not configured")
        raise RuntimeError("PATENTE_HASH not configured")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if not hmac.compare_digest(token_hash, expected_hash):
        logger.error(f"Sovereign Auth Failure: Invalid token for {entity_id}")
        raise PermissionError("Invalid patente token")

    # Scope-Based Access Control (SBAC)
    # Standard Scopes: AIRPORT_OPS, PORT_OPS, FUEL_ACCESS, ADMIN

    # Admin bypass for all scopes
    if entity_id.startswith("ADMIN_"):
        return True

    if required_scope == "AIRPORT_OPS":
        allowed = any(entity_id.startswith(pre) for pre in ["FLGT", "CAPT", "STAF"])
    elif required_scope == "PORT_OPS":
        allowed = any(entity_id.startswith(pre) for pre in ["VESL", "CAPT"])
    elif required_scope == "FUEL_ACCESS":
        allowed = entity_id.startswith("CAPT") or entity_id.startswith("STAF_FUEL")
    elif required_scope == "ADMIN":
        allowed = entity_id.startswith("ADMIN")
    else:
        allowed = False

    if not allowed:
        logger.error(f"Sovereign Scope Denied: {entity_id} attempted {required_scope}")
        return False

    return True

class NexGenPatenteVerifier:
    """
    Production wrapper for NexGenPatenteVerifier
    """
    @staticmethod
    def authorize_access(token: str, entity_id: str, required_scope: str) -> bool:
        return authorize_access(token, entity_id, required_scope)

    @staticmethod
    def _get_secret():
        return os.getenv("NEXGEN_SECRET", "NEXGEN_SECRET_DEFAULT")

    @staticmethod
    def verify_patente(entity_id: str, patente_key: str, entity_type: str) -> bool:
        secret = NexGenPatenteVerifier._get_secret()
        expected_key = hashlib.sha256(f"{entity_id}:{secret}".encode()).hexdigest()
        return hmac.compare_digest(patente_key, expected_key)

    @staticmethod
    def generate_patente(entity_id: str) -> str:
        secret = NexGenPatenteVerifier._get_secret()
        return hashlib.sha256(f"{entity_id}:{secret}".encode()).hexdigest()

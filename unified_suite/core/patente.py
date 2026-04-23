import hashlib
import hmac
import os
import logging

logger = logging.getLogger("unified_suite")

def authorize_access(token: str, entity_id: str, required_scope: str):
    """
    AEGIS-GRADE AUTHORIZATION (MNOS-COMPLIANT)
    Enforces SHA256 token validation, entity binding, and Scope-Based Access Control (SBAC).
    """
    if not token:
        logger.error(f"Sovereign Auth Failure: Missing token for {entity_id}")
        raise PermissionError("Missing patente token")

    # 1. TOKEN AUTHENTICATION (HMAC/SHA256)
    # AEGIS Doctrine: Verification via Shared Sovereign Secret
    secret = os.getenv("NEXGEN_SECRET", "dev_fallback_secret")

    # Expected token format: entity_id:HMAC(entity_id, secret)
    if ":" not in token:
        logger.error(f"Sovereign Auth Failure: Malformed token for {entity_id}")
        raise PermissionError("Invalid patente token format")

    token_entity, token_sig = token.split(":", 1)

    # 2. ENTITY BINDING (AEGIS Doctrine)
    if token_entity != entity_id and not entity_id.startswith("ADMIN"):
         logger.error(f"Sovereign Binding Failure: Token entity mismatch {token_entity} != {entity_id}")
         raise PermissionError(f"Patente token not bound to entity {entity_id}")

    # 3. SIGNATURE VERIFICATION
    expected_sig = hmac.new(secret.encode(), token_entity.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token_sig, expected_sig):
        logger.error(f"Sovereign Auth Failure: Invalid token signature for {entity_id}")
        raise PermissionError("Invalid patente token signature")

    # 3. SCOPE-BASED ACCESS CONTROL (SBAC)
    # Standard Scopes: AIRPORT_OPS, PORT_OPS, FUEL_ACCESS, ADMIN

    # Admin bypass for all scopes
    if entity_id.startswith("ADMIN"):
        return True

    if required_scope == "AIRPORT_OPS":
        allowed = any(entity_id.startswith(pre) for pre in ["FLGT", "CAPT", "STAF", "EK", "QR", "EY", "TMA", "MANTA", "Q2"])
    elif required_scope == "PORT_OPS":
        allowed = any(entity_id.startswith(pre) for pre in ["VESL", "CAPT", "MSC", "MAERSK", "COSCO", "V_"])
    elif required_scope == "FUEL_ACCESS":
        allowed = any(entity_id.startswith(pre) for pre in ["CAPT", "STAF_FUEL", "FLGT"])
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
        sig = hmac.new(secret.encode(), entity_id.encode(), hashlib.sha256).hexdigest()
        return f"{entity_id}:{sig}"

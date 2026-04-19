import hashlib
import os
import logging

logger = logging.getLogger("unified_suite")

def authorize_access(token: str, entity_id: str = None, area: str = None):
    """
    Enforce Patente Authorization (MQAP COMPLIANT)
    """
    if not token:
        logger.error("Authorization failed: Missing patente token")
        raise PermissionError("Missing patente token")

    expected_hash = os.getenv("PATENTE_HASH")

    if not expected_hash:
        # Non-breaking behavior: log warning but do NOT allow silent bypass
        logger.warning("System alert: PATENTE_HASH not configured")
        raise RuntimeError("PATENTE_HASH not configured")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    if token_hash != expected_hash:
        logger.error("Authorization failed: Invalid patente token")
        raise PermissionError("Invalid patente token")

    # Compatibility: Maintain EBAC if entity_id and area are provided
    if entity_id and area:
        if entity_id.startswith("CAPT"):
            allowed = area in ["DOCKING_AREA", "GATE_AREA"]
        elif entity_id.startswith("STAF"):
            allowed = area == "GATE_AREA"
        elif entity_id.startswith("VESL"):
            allowed = area == "DOCKING_AREA"
        elif entity_id.startswith("FLGT"):
            allowed = area == "GATE_AREA"
        else:
            allowed = False

        if not allowed:
            logger.error(f"Access denied: Entity {entity_id} not authorized for {area}")
            return False

    return True

class NexGenPatenteVerifier:
    """
    Legacy wrapper for NexGenPatenteVerifier
    """
    @staticmethod
    def authorize_access(token: str, entity_id: str = None, area: str = None) -> bool:
        return authorize_access(token, entity_id, area)

    @staticmethod
    def _get_secret():
        return os.getenv("NEXGEN_SECRET", "NEXGEN_SECRET_DEFAULT")

    @staticmethod
    def verify_patente(entity_id: str, patente_key: str, entity_type: str) -> bool:
        secret = NexGenPatenteVerifier._get_secret()
        expected_key = hashlib.sha256(f"{entity_id}:{secret}".encode()).hexdigest()
        return patente_key == expected_key

    @staticmethod
    def generate_patente(entity_id: str) -> str:
        secret = NexGenPatenteVerifier._get_secret()
        return hashlib.sha256(f"{entity_id}:{secret}".encode()).hexdigest()

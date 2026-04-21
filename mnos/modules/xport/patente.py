import hashlib
import hmac
import os
import logging

logger = logging.getLogger("mnos.xport")

class PatenteVerifier:
    """
    Sovereign Identity & Licensing Adapter (XPORT v2)
    Enforces AEGIS-grade token verification and mandatory scope checks.
    """

    @staticmethod
    def verify_access(token: str, entity_id: str, required_scope: str) -> bool:
        """
        Production Token Verification:
        - Must be present
        - Must follow entity_id:HMAC(entity_id, secret) format
        - Must contain required scope (airport.ops, port.master)
        """
        if not token:
            logger.error(f"Patente Failure: Missing token for {entity_id}")
            raise PermissionError("Identity verification failed: Missing patente")

        secret = os.getenv("NEXGEN_SECRET", "dev_fallback_secret")

        # 1. FORMAT VALIDATION
        if ":" not in token:
            logger.error(f"Patente Failure: Malformed token for {entity_id}")
            raise PermissionError("Identity verification failed: Malformed token")

        token_entity, token_sig = token.split(":", 1)

        # 2. ENTITY BINDING
        if token_entity != entity_id and not entity_id.startswith("ADMIN"):
            logger.error(f"Patente Failure: Binding violation {token_entity} != {entity_id}")
            raise PermissionError(f"Identity verification failed: Token not bound to {entity_id}")

        # 3. SIGNATURE VERIFICATION (AEGIS Doctrine)
        expected_sig = hmac.new(secret.encode(), token_entity.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(token_sig, expected_sig):
            logger.error(f"Patente Failure: Signature invalid for {entity_id}")
            raise PermissionError("Identity verification failed: Invalid signature")

        # 4. SCOPE ENFORCEMENT
        # Scopes: airport.ops, port.master, fuel.access
        allowed_prefixes = {
            "airport.ops": ["FLGT", "CAPT", "STAF", "EK", "QR", "EY", "TMA", "MANTA", "Q2"],
            "port.master": ["VESL", "CAPT", "MSC", "MAERSK", "COSCO", "V_"],
            "fuel.access": ["CAPT", "STAF_FUEL", "FLGT"]
        }

        # Admin bypass
        if entity_id.startswith("ADMIN"):
            return True

        prefixes = allowed_prefixes.get(required_scope, [])
        if not any(entity_id.startswith(pre) for pre in prefixes):
            logger.error(f"Patente Failure: Scope violation. {entity_id} attempted {required_scope}")
            return False

        logger.info(f"Patente Verified: {entity_id} granted {required_scope}")
        return True

    @staticmethod
    def generate_token(entity_id: str) -> str:
        """
        Internal utility for simulation and bootstrap.
        """
        secret = os.getenv("NEXGEN_SECRET", "dev_fallback_secret")
        sig = hmac.new(secret.encode(), entity_id.encode(), hashlib.sha256).hexdigest()
        return f"{entity_id}:{sig}"

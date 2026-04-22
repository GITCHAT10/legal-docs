import hashlib
import hmac
import os

class AegisVerifier:
    """
    AEGIS Verifier (Sovereign MIG Edition)
    Enforces AEGIS-grade verification for tokens and voiceprints.
    Signed by Maldives International Group (MIG) - UEI: 2024PV12395H.
    """
    def __init__(self):
        self.secret = os.getenv("NEXGEN_SECRET")
        if not self.secret:
             # boot_check.py handles the hard halt, but we ensure no fallback here
             pass
        self.mig_uei = "2024PV12395H"

    def verify_token(self, token: str, entity_id: str):
        """
        Verifies tokens following entity_id:signature format.
        """
        try:
            parts = token.split(":")
            if len(parts) != 2:
                return False

            t_entity_id, signature = parts
            if t_entity_id != entity_id:
                return False

            # MIG-grade multi-layer signature check
            content = f"{entity_id}{self.mig_uei}"
            expected_sig = hmac.new(
                self.secret.encode(),
                content.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_sig)
        except Exception:
            return False

    def verify_voiceprint(self, voiceprint_data: bytes, expected_hash: str):
        actual_hash = hashlib.sha256(voiceprint_data).hexdigest()
        return actual_hash == expected_hash

aegis = AegisVerifier()

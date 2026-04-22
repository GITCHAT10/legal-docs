import hashlib
import hmac
import os

class AegisVerifier:
    """
    AEGIS Verifier
    Enforces AEGIS-grade verification for tokens and voiceprints.
    """
    def __init__(self):
        self.secret = os.getenv("NEXGEN_SECRET", "default_secret")

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

            expected_sig = hmac.new(
                self.secret.encode(),
                entity_id.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_sig)
        except Exception:
            return False

    def verify_voiceprint(self, voiceprint_data: bytes, expected_hash: str):
        """
        Simple simulation of voiceprint match score check.
        """
        actual_hash = hashlib.sha256(voiceprint_data).hexdigest()
        # In a real system, we'd use a machine learning model to get a match score >= 0.96
        return actual_hash == expected_hash

aegis = AegisVerifier()

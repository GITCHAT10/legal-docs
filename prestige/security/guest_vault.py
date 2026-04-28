from cryptography.fernet import Fernet
import os, structlog
from decimal import Decimal

logger = structlog.get_logger()

class GuestIntelVault:
    """
    Internal: GUEST_VAULT
    External: Prestige Guest Intelligence Shield

    Encrypts high-value guest signals before storage.
    Only decrypted for FCE-validated pricing decisions.
    """
    def __init__(self):
        # Key stored in secure env var: PRESTIGE_INTEL_KEY
        self.key = os.getenv("PRESTIGE_INTEL_KEY", Fernet.generate_key())
        if isinstance(self.key, str):
            self.key = self.key.encode()
        self.cipher = Fernet(self.key)

    def encrypt_guest_intel(self, intel: dict) -> bytes:
        """Encrypt sensitive guest data (net worth, intent, preferences)"""
        import json
        payload = json.dumps(intel).encode()
        return self.cipher.encrypt(payload)

    def decrypt_guest_intel(self, encrypted: bytes) -> dict:
        """Decrypt only for authorized pricing/EXMAIL decisions"""
        import json
        decrypted = self.cipher.decrypt(encrypted).decode()
        return json.loads(decrypted)

    def score_guest_value(self, decrypted_intel: dict) -> Decimal:
        """Convert intel to pricing context (never expose raw data)"""
        base_score = Decimal("1.0")
        if decrypted_intel.get("net_worth") == "Ultra":
            base_score += Decimal("0.3")
        if decrypted_intel.get("intent") in ["New Year Suite", "Private Yacht"]:
            base_score += Decimal("0.2")
        if decrypted_intel.get("privacy_required"):
            base_score += Decimal("0.15")
        return min(base_score, Decimal("2.0"))  # Cap at 2x multiplier

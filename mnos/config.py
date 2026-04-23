import os
from decimal import Decimal

class Config:
    # Sovereign Secrets
    NEXGEN_SECRET = os.getenv("NEXGEN_SECRET")
    if not NEXGEN_SECRET:
        raise RuntimeError("NEXGEN_SECRET environment variable is MANDATORY.")

    MNOS_INTEGRATION_SECRET = os.getenv("MNOS_INTEGRATION_SECRET", "mnos_default_secret")

    # Financial Logic (Maldives Doctrine)
    SERVICE_CHARGE = Decimal("0.10") # 10%
    TGST = Decimal("0.17")           # 17%
    GREEN_TAX_USD = Decimal("6.00")   # $6/pax/night

    # AI Thresholds
    SILVIA_INTENT_MIN = 0.90
    SILVIA_CONFIDENCE_MIN = 0.85
    AEGIS_VOICEPRINT_MIN = 0.96

    # Resilience
    S3_BACKUP_BUCKET = os.getenv("S3_BACKUP_BUCKET", "nexus-sky-i-backups")
    SNAPSHOT_RETENTION_DAYS = 30

    # Jurisdictions
    DEFAULT_JURISDICTION = "MV"

    # AIGShadow Root Anchors
    GENESIS_PREVIOUS_HASH = "0" * 64
    CORE_V1_ROOT_HASH = "9f92f77a89c6c5e5ad289fd790b195c48c52fc763f8fd8a71936d5c924315f89"

config = Config()

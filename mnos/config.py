import os
from decimal import Decimal
from datetime import datetime

class Config:
    # Sovereign Secrets
    NEXGEN_SECRET = os.getenv("NEXGEN_SECRET")
    if not NEXGEN_SECRET:
        raise RuntimeError("NEXGEN_SECRET environment variable is MANDATORY.")

    MNOS_INTEGRATION_SECRET = os.getenv("MNOS_INTEGRATION_SECRET", "mnos_default_secret")

    # Financial Logic (Maldives Doctrine)
    SERVICE_CHARGE = Decimal("0.10") # 10%

    # TGST Transition Rule: 17% from 2025-07-01
    TGST_TRANSITION_DATE = datetime(2025, 7, 1)
    TGST_PRE_TRANSITION = Decimal("0.16") # Assuming 16% legacy
    TGST_POST_TRANSITION = Decimal("0.17")

    GREEN_TAX_RESORT_USD = Decimal("6.00")   # $6/pax/night for resorts/vessels
    GREEN_TAX_GUESTHOUSE_USD = Decimal("3.00") # $3/pax/night for guesthouses
    GREEN_TAX_USD = GREEN_TAX_RESORT_USD # Default/Legacy compatibility

    # AI Thresholds
    SILVIA_INTENT_MIN = 0.90
    SILVIA_CONFIDENCE_MIN = 0.85
    AEGIS_VOICEPRINT_MIN = 0.96

    # Resilience
    S3_BACKUP_BUCKET = os.getenv("S3_BACKUP_BUCKET", "nexus-sky-i-backups")
    SNAPSHOT_RETENTION_DAYS = 30

    # Jurisdictions
    DEFAULT_JURISDICTION = "MV"

config = Config()

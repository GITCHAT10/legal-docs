from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, UTC
import hashlib
import json

class UCONationalCredential(BaseModel):
    """Sovereign credential with Maldives-specific fields"""
    credential_id: str
    tier: str # BCA, BCO, BCC, BCD
    recipient_hash: str
    mnu_program: Optional[str]
    atoll_origin: str # e.g., KA, GA, MLE
    pillar_scores: Dict[str, float]
    bcsi_total: float
    issued_at: datetime
    ministry_endorsed: bool = True
    pdpa_compliant: bool = True

    def to_ministry_export(self) -> Dict:
        return {
            "credential_id": self.credential_id,
            "tier": self.tier,
            "atoll_origin": self.atoll_origin,
            "bcsi_total": self.bcsi_total,
            "pillar_summary": {k: v for k, v in self.pillar_scores.items() if v >= 80},
            "issued_at": self.issued_at.isoformat(),
            "ministry_verified": self.ministry_endorsed,
            "pdpa_anonymized": True
        }

class NationalCredentialManager:
    """
    Manages issuance of UCO-National credentials.
    Anchors every issuance to the SHADOW ledger.
    """
    def __init__(self, core):
        self.core = core
        self.issued_credentials = {}

    def issue_national_uco(self, trainee_id: str, bcsi_data: dict, mnu_program: str = None, atoll: str = "MLE"):
        issued_at = datetime.now(UTC)
        credential_id = f"UCO-MV-{bcsi_data['eligible_tier']}-{trainee_id[:8].upper()}"
        recipient_hash = hashlib.sha256(f"national_id:{trainee_id}".encode()).hexdigest()

        uco = UCONationalCredential(
            credential_id=credential_id,
            tier=bcsi_data["eligible_tier"] or "BCA",
            recipient_hash=recipient_hash,
            mnu_program=mnu_program,
            atoll_origin=atoll,
            pillar_scores=bcsi_data["breakdown"]["pillars"],
            bcsi_total=bcsi_data["bcsi_score"],
            issued_at=issued_at
        )

        # Anchor to SHADOW - Model dump with ISO formats for datetime
        from mnos.shared.execution_guard import _sovereign_context
        token = _sovereign_context.set({"token": "UCO-NAT-MINT", "actor": {"identity_id": "SYSTEM", "system_override": True}})
        try:
            # We must use mode='json' or manual conversion for shadow.commit
            self.core.shadow.commit(
                "education.national_uco.minted",
                trainee_id,
                uco.model_dump(mode='json')
            )
        finally:
            _sovereign_context.reset(token)

        self.issued_credentials[credential_id] = uco
        return uco

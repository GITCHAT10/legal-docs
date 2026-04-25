from sqlalchemy.orm import Session
from united_transfer_system import models
import logging

class TrustLock:
    """
    Sovereign Execution: Partner Trust Lock.
    Calculates trust scores and assigns tiers.
    """
    TIER_LIMITS = {
        models.PartnerTier.ELITE: 1000,
        models.PartnerTier.HARDENED: 300,
        models.PartnerTier.STABILIZING: 50,
        models.PartnerTier.RESTRICTED: 0
    }

    def update_partner_score(self, db: Session, partner_id: int, journey_success: bool):
        partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
        if not partner:
            return

        # Simple trust score adjustment
        if journey_success:
            partner.trust_score = min(1.0, partner.trust_score + 0.05)
        else:
            partner.trust_score = max(0.0, partner.trust_score - 0.2)

        # Tier assignment logic
        if partner.trust_score >= 0.95:
            partner.tier = models.PartnerTier.ELITE
        elif partner.trust_score >= 0.8:
            partner.tier = models.PartnerTier.HARDENED
        elif partner.trust_score >= 0.5:
            partner.tier = models.PartnerTier.STABILIZING
        else:
            partner.tier = models.PartnerTier.RESTRICTED

        partner.max_daily_volume = self.TIER_LIMITS[partner.tier]
        db.commit()

    def can_assign_job(self, db: Session, partner_id: int) -> bool:
        partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
        if not partner or partner.tier == models.PartnerTier.RESTRICTED:
            return False

        # Check current volume (simplified)
        return True

trust_lock = TrustLock()

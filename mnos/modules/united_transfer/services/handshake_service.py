from sqlalchemy.orm import Session
from mnos.modules.united_transfer import models
from mnos.modules.fce import service as fce_service
import uuid

def trigger_safe_arrival(db_id: int):
    # This would be called as a background task, needs its own session handling if not passed
    # For now assuming session is handled or using a global one for simplicity in sandbox
    pass

def verify_dual_qr(db: Session, leg_id: int, scan_data: str, actor: str):
    leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
    if not leg:
        return {"error": "Leg not found"}

    if leg.master_voucher_code == scan_data:
        # Instant Payout Logic
        _execute_instant_payout(db, leg, actor)
        return {"status": "verified", "payout": "executed"}

    return {"error": "Invalid QR"}

def _execute_instant_payout(db: Session, leg: models.Leg, actor: str):
    # Payment releases to the driver's wallet the micro-second the scan is verified
    wallet = db.query(models.Wallet).filter(models.Wallet.owner_id == leg.provider_id).first()
    if not wallet:
        wallet = models.Wallet(owner_id=leg.provider_id, balance=0.0)
        db.add(wallet)
        db.flush()

    payout_amount = 100.0 # Placeholder
    wallet.balance += payout_amount

    transaction = models.Transaction(
        wallet_id=wallet.id,
        trace_id=f"PAY-{uuid.uuid4().hex[:8]}",
        amount=payout_amount,
        type="PAYOUT",
        leg_id=leg.id
    )
    db.add(transaction)
    db.commit()

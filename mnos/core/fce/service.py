from typing import Dict, Optional, Any, List
from sqlalchemy.orm import Session
from mnos.core.fce import models
import uuid
from datetime import datetime, date
from .tax_logic import calculate_maldives_taxes
from mnos.core.shadow import service as shadow_service
from mnos.core.eleone import eleone

def open_folio(db: Session, reservation_id: str, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM", guest_id: int = None) -> models.Folio:
    try:
        # 1. VALIDATE
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id, models.Folio.tenant_id == tenant_id).first()
        if existing: return existing

        # 2. DECIDE (ELEONE)
        if not eleone.decide_action(db, "OPEN_FOLIO", {"reservation_id": reservation_id}):
            raise RuntimeError("ELEONE denied folio creation")

        # 3. DB WRITE
        folio = models.Folio(
            tenant_id=tenant_id,
            trace_id=trace_id,
            guest_id=guest_id,
            external_reservation_id=reservation_id,
            status=models.FolioStatus.OPEN,
            created_by=actor
        )
        db.add(folio)
        db.flush()

        # 5. SHADOW COMMIT
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "OPEN_FOLIO",
            "entity_type": "FOLIO",
            "entity_id": folio.id,
            "after_state": {"reservation_id": reservation_id, "status": folio.status, "guest_id": guest_id}
        })

        db.commit()
        db.refresh(folio)
        return folio
    except Exception:
        db.rollback()
        raise

def reverse_charge(db: Session, line_id: int, trace_id: str, actor: str = "SYSTEM") -> models.FolioLine:
    """
    Hardened Reversal: Zero destructive edits.
    Creates a Credit Note entry (Negative Charge) linked to the original.
    """
    try:
        original = db.query(models.FolioLine).filter(models.FolioLine.id == line_id).first()
        if not original: raise ValueError("Original charge not found")
        if original.is_reversed: raise ValueError("Charge already reversed")

        folio = db.query(models.Folio).filter(models.Folio.id == original.folio_id).first()

        # Create Reversal Line (Credit Note)
        reversal = models.FolioLine(
            tenant_id=original.tenant_id,
            trace_id=trace_id,
            folio_id=original.folio_id,
            type=original.type,
            base_amount=-original.base_amount,
            service_charge=-original.service_charge,
            tgst=-original.tgst,
            green_tax=-original.green_tax,
            amount=-original.amount,
            currency=original.currency,
            description=f"REVERSAL OF {original.trace_id}: {original.description}",
            is_reversed=False, # This is the reversal itself
            reversal_of_entry_id=original.id,
            created_by=actor
        )
        db.add(reversal)

        original.is_reversed = True

        before_state = {"total_amount": folio.total_amount}
        folio.total_amount += reversal.amount
        db.add(folio)
        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "REVERSE_CHARGE",
            "entity_type": "FOLIO_LINE",
            "entity_id": reversal.id,
            "linked_entity_id": original.id,
            "before_state": before_state,
            "after_state": {"amount": reversal.amount, "folio_total": folio.total_amount}
        })

        db.commit()
        db.refresh(reversal)
        return reversal
    except Exception:
        db.rollback()
        raise

def issue_refund(db: Session, folio_id: int, refund_data: Dict, trace_id: str, actor: str = "SYSTEM") -> models.FolioTransaction:
    """
    Hardened Refund: Negative transaction to balance the ledger.
    """
    try:
        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError("Folio not found")

        amount = refund_data["amount"]
        if amount > 0: amount = -amount # Ensure it's a negative payout

        transaction = models.FolioTransaction(
            tenant_id=folio.tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            amount=amount,
            method=refund_data.get("method", "REFUND"),
            currency=refund_data.get("currency", "USD"),
            status=models.TransactionStatus.POSTED,
            created_by=actor
        )
        db.add(transaction)

        before_state = {"paid_amount": folio.paid_amount}
        folio.paid_amount += transaction.amount # Adding a negative
        db.add(folio)
        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "ISSUE_REFUND",
            "entity_type": "FOLIO_TRANSACTION",
            "entity_id": transaction.id,
            "before_state": before_state,
            "after_state": {"amount": transaction.amount, "folio_paid": folio.paid_amount}
        })

        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        raise

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioLine:
    try:
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id, models.FolioLine.tenant_id == tenant_id).first()
        if existing: return existing

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError(f"Folio {folio_id} not found")

        if not eleone.decide_action(db, "POST_CHARGE", {"folio_id": folio_id, "amount": charge_data.get("base_amount")}):
             raise RuntimeError("ELEONE denied charge posting")

        biz_date = charge_data.get("business_date")
        if isinstance(biz_date, str): biz_date = date.fromisoformat(biz_date)
        elif not biz_date: biz_date = date.today()

        currency = charge_data.get("currency", "USD")
        exchange_rate = 1.0
        if currency != "USD":
            rate_lock = db.query(models.ExchangeRateLock).filter(
                models.ExchangeRateLock.target_currency == currency,
                models.ExchangeRateLock.expires_at > datetime.utcnow()
            ).first()
            if rate_lock:
                exchange_rate = rate_lock.rate

        if charge_data.get("is_tax_adjustment"):
            taxes = {
                "base_amount": charge_data.get("base_amount", 0.0),
                "service_charge": charge_data.get("service_charge", 0.0),
                "tgst": charge_data.get("tgst", 0.0),
                "green_tax": charge_data.get("green_tax", 0.0),
                "total_amount": charge_data.get("base_amount", 0.0) +
                                charge_data.get("service_charge", 0.0) +
                                charge_data.get("tgst", 0.0) +
                                charge_data.get("green_tax", 0.0)
            }
        else:
            taxes = calculate_maldives_taxes(
                charge_data["base_amount"],
                biz_date,
                charge_data.get("apply_green_tax", False),
                charge_data.get("nights", 0),
                currency=currency,
                exchange_rate=exchange_rate
            )

        line = models.FolioLine(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            type=charge_data["type"],
            base_amount=taxes["base_amount"],
            service_charge=taxes["service_charge"],
            tgst=taxes["tgst"],
            green_tax=taxes["green_tax"],
            amount=taxes["total_amount"],
            currency=currency,
            exchange_rate=exchange_rate,
            description=charge_data.get("description"),
            created_by=actor
        )
        db.add(line)

        before_state = {"total_amount": folio.total_amount}
        folio.total_amount += line.amount
        db.add(folio)
        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "POST_CHARGE",
            "entity_type": "FOLIO_LINE",
            "entity_id": line.id,
            "before_state": before_state,
            "after_state": {"amount": line.amount, "folio_total": folio.total_amount, "currency": currency}
        })

        db.commit()
        db.refresh(line)
        return line
    except Exception:
        db.rollback()
        raise

def post_transaction(db: Session, folio_id: int, payment_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioTransaction:
    try:
        if not trace_id: raise ValueError("trace_id required")
        existing = db.query(models.FolioTransaction).filter(models.FolioTransaction.trace_id == trace_id, models.FolioTransaction.tenant_id == tenant_id).first()
        if existing: return existing

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError(f"Folio {folio_id} not found")

        transaction = models.FolioTransaction(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=folio_id,
            amount=payment_data["amount"],
            method=payment_data["method"],
            currency=payment_data.get("currency", "USD"),
            status=models.TransactionStatus.POSTED,
            created_by=actor
        )
        db.add(transaction)

        before_state = {"paid_amount": folio.paid_amount}
        # In a real clearing house, we'd convert payment amount to folio currency if they differ
        folio.paid_amount += transaction.amount
        db.add(folio)
        db.flush()

        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "POST_TRANSACTION",
            "entity_type": "FOLIO_TRANSACTION",
            "entity_id": transaction.id,
            "before_state": before_state,
            "after_state": {"amount": transaction.amount, "folio_paid": folio.paid_amount}
        })

        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        raise

def cross_property_settlement(db: Session, guest_id: int, trace_id: str, actor: str = "SYSTEM") -> List[Dict]:
    """
    Global Clearing House: Settle all OPEN folios for a guest across the property network.
    """
    try:
        folios = db.query(models.Folio).filter(
            models.Folio.guest_id == guest_id,
            models.Folio.status == models.FolioStatus.OPEN
        ).all()

        results = []
        for folio in folios:
            # Simple settlement: Pay the full balance
            balance = folio.total_amount - folio.paid_amount
            if balance > 0:
                tx = post_transaction(db, folio.id, {
                    "amount": balance,
                    "method": "CROSS_PROPERTY_SETTLEMENT",
                    "currency": folio.currency
                }, f"SETTLE-{folio.id}-{trace_id}", folio.tenant_id, actor)
                results.append({"folio_id": folio.id, "tenant_id": folio.tenant_id, "amount": balance, "status": "SETTLED"})

        return results
    except Exception:
        db.rollback()
        raise

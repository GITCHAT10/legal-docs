from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from mnos.modules.fce import models
from .service import post_charge
import uuid
from datetime import datetime

class FolioLockedException(Exception):
    pass

def verify_folio_modifiable(db: Session, folio_id: int):
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if not folio:
        return
    if folio.status == models.FolioStatus.FINALIZED:
        raise FolioLockedException("Cannot modify a finalized folio")

def void_charge(db: Session, line_id: int, reason: str, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.FolioLine:
    try:
        line = db.query(models.FolioLine).filter(models.FolioLine.id == line_id).first()
        if not line:
            raise ValueError("Charge line not found")

        verify_folio_modifiable(db, line.folio_id)

        if line.is_reversed:
            raise ValueError("Charge already reversed")

        # Create reversal line
        reversal_line = models.FolioLine(
            tenant_id=tenant_id,
            trace_id=trace_id,
            folio_id=line.folio_id,
            type=line.type,
            base_amount=-line.base_amount,
            service_charge=-line.service_charge,
            tgst=-line.tgst,
            green_tax=-line.green_tax,
            amount=-line.amount,
            description=f"REVERSAL: {reason} (Original: {line.description})",
            is_reversed=True,
            created_by=actor
        )
        db.add(reversal_line)

        line.is_reversed = True

        folio = db.query(models.Folio).filter(models.Folio.id == line.folio_id).first()
        folio.total_amount += reversal_line.amount

        # Ledger Entry for reversal
        ledger = models.LedgerEntry(
            tenant_id=tenant_id,
            trace_id=f"rev-ledger-{trace_id}",
            account_code="REVENUE_ADJUST",
            debit=-reversal_line.amount,
            description=f"Reversal of charge {line_id}",
            created_by=actor
        )
        db.add(ledger)

        db.commit()
        db.refresh(reversal_line)
        return reversal_line
    except Exception:
        db.rollback()
        raise

def split_folio(db: Session, source_folio_id: int, target_reservation_id: str, line_ids: List[int], trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> models.Folio:
    try:
        source_folio = db.query(models.Folio).filter(models.Folio.id == source_folio_id).first()
        if not source_folio:
            raise ValueError("Source folio not found")

        verify_folio_modifiable(db, source_folio_id)

        # Create target folio
        target_folio = models.Folio(
            tenant_id=tenant_id,
            trace_id=trace_id,
            external_reservation_id=target_reservation_id,
            status=models.FolioStatus.OPEN,
            created_by=actor
        )
        db.add(target_folio)
        db.flush() # Get target_folio.id

        total_moved = 0.0
        for lid in line_ids:
            line = db.query(models.FolioLine).filter(models.FolioLine.id == lid, models.FolioLine.folio_id == source_folio_id).first()
            if line:
                line.folio_id = target_folio.id
                total_moved += line.amount

        source_folio.total_amount -= total_moved
        target_folio.total_amount = total_moved

        db.commit()
        db.refresh(target_folio)
        return target_folio
    except Exception:
        db.rollback()
        raise

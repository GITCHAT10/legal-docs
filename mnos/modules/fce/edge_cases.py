from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from mnos.modules.fce import models
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
    """
    Explicit Reversal Doctrine: correcting entries must be counter-entries.
    """
    try:
        line = db.query(models.FolioLine).filter(models.FolioLine.id == line_id).first()
        if not line:
            raise ValueError("Charge line not found")

        verify_folio_modifiable(db, line.folio_id)

        if line.is_reversed:
            raise ValueError("Charge already reversed")

        # 1. Create Counter-Entry (Counter-Signal)
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
            description=f"REVERSAL: {reason} (Ref: {line.id})",
            is_reversed=True,
            created_by=actor
        )
        db.add(reversal_line)

        # Mark original as reversed (linked)
        line.is_reversed = True

        folio = db.query(models.Folio).filter(models.Folio.id == line.folio_id).first()
        folio.total_amount += reversal_line.amount

        # 2. Ledger Linked Counter-Entry
        ledger = models.LedgerEntry(
            tenant_id=tenant_id,
            trace_id=f"rev-ledger-{trace_id}",
            account_code="REVENUE_REVERSAL",
            debit=-reversal_line.amount,
            description=f"Counter-entry for line {line_id}",
            created_by=actor
        )
        db.add(ledger)

        db.commit()
        db.refresh(reversal_line)
        return reversal_line
    except Exception:
        db.rollback()
        raise

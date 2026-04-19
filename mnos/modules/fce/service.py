from typing import Dict, Optional
from sqlalchemy.orm import Session
from mnos.modules.fce import models
import uuid

# MIRA compliant rates
SERVICE_CHARGE_RATE = 0.10
TGST_RATE = 0.17
GREEN_TAX_USD = 6.0

def validate_maldives_tax(base_amount: float, apply_green_tax: bool = False, nights: int = 0) -> Dict:
    sc = base_amount * SERVICE_CHARGE_RATE
    tgst = (base_amount + sc) * TGST_RATE
    gt = GREEN_TAX_USD * nights if apply_green_tax else 0.0
    return {
        "base": base_amount,
        "sc": sc,
        "tgst": tgst,
        "green_tax": gt,
        "total": base_amount + sc + tgst + gt
    }

def open_folio(db: Session, reservation_id: str, trace_id: str) -> models.Folio:
    existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id).first()
    if existing:
        return existing

    folio = models.Folio(
        external_reservation_id=reservation_id,
        trace_id=trace_id,
        status=models.FolioStatus.OPEN
    )
    db.add(folio)
    db.commit()
    db.refresh(folio)
    return folio

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str) -> models.FolioLine:
    existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id).first()
    if existing:
        return existing

    taxes = validate_maldives_tax(
        charge_data["base_amount"],
        charge_data.get("apply_green_tax", False),
        charge_data.get("nights", 0)
    )

    line = models.FolioLine(
        folio_id=folio_id,
        trace_id=trace_id,
        type=charge_data["type"],
        base_amount=taxes["base"],
        service_charge=taxes["sc"],
        tgst=taxes["tgst"],
        green_tax=taxes["green_tax"],
        total_amount=taxes["total"],
        description=charge_data.get("description")
    )
    db.add(line)

    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    folio.total_amount += line.total_amount
    db.add(folio)

    # Record in ledger
    ledger = models.LedgerEntry(
        trace_id=f"ledger-{trace_id}",
        account_code="REVENUE",
        credit=line.total_amount,
        description=f"Charge for folio {folio_id}"
    )
    db.add(ledger)

    db.commit()
    db.refresh(line)
    return line

def finalize_invoice(db: Session, folio_id: int) -> models.Invoice:
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    if folio.status == models.FolioStatus.FINALIZED:
        return folio.invoices[0]

    invoice = models.Invoice(
        folio_id=folio_id,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        total_amount=folio.total_amount,
        tax_summary={
            "sc": sum(l.service_charge for l in folio.lines),
            "tgst": sum(l.tgst for l in folio.lines),
            "green_tax": sum(l.green_tax for l in folio.lines)
        }
    )
    db.add(invoice)
    folio.status = models.FolioStatus.FINALIZED
    db.add(folio)
    db.commit()
    db.refresh(invoice)
    return invoice

def reverse_charge(db: Session, line_id: int, trace_id: str) -> Optional[models.FolioLine]:
    line = db.query(models.FolioLine).filter(models.FolioLine.id == line_id).first()
    if not line or line.is_reversed:
        return line

    # Create reversal line
    reversal = models.FolioLine(
        folio_id=line.folio_id,
        trace_id=trace_id,
        type=line.type,
        base_amount=-line.base_amount,
        service_charge=-line.service_charge,
        tgst=-line.tgst,
        green_tax=-line.green_tax,
        total_amount=-line.total_amount,
        description=f"Reversal of {line.id}",
        is_reversed=True
    )
    db.add(reversal)
    line.is_reversed = True

    folio = db.query(models.Folio).filter(models.Folio.id == line.folio_id).first()
    folio.total_amount += reversal.total_amount
    db.add(folio)

    db.commit()
    db.refresh(reversal)
    return reversal

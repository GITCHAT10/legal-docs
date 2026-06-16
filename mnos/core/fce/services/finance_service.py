from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from . import models_finance
from datetime import date, datetime
import uuid

def get_next_invoice_number(db: Session, prefix: str = "INV") -> str:
    seq = db.query(models_finance.InvoiceSequence).filter(models_finance.InvoiceSequence.prefix == prefix).first()
    if not seq:
        seq = models_finance.InvoiceSequence(prefix=prefix, last_value=0)
        db.add(seq)
        db.flush()

    seq.last_value += 1
    # db.commit() # Removed commit, let service layer handle it
    return f"{prefix}-{date.today().year}-{seq.last_value:06d}"

def perform_night_audit(db: Session, business_date: date, user_id: str):
    period = db.query(models_finance.FinancialPeriod).filter(models_finance.FinancialPeriod.business_date == business_date).first()
    if not period:
        period = models_finance.FinancialPeriod(business_date=business_date)
        db.add(period)

    if period.is_closed:
        raise ValueError(f"Period {business_date} is already closed")

    period.is_closed = True
    period.closed_at = datetime.utcnow()
    period.closed_by = user_id

    from datetime import timedelta
    next_date = business_date + timedelta(days=1)
    next_period = models_finance.FinancialPeriod(business_date=next_date)
    db.add(next_period)

def verify_period_open(db: Session, target_date: date):
    period = db.query(models_finance.FinancialPeriod).filter(models_finance.FinancialPeriod.business_date == target_date).first()
    if period and period.is_closed:
        raise ValueError(f"Financial period {target_date} is closed for posting")

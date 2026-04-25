from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime, UTC
from decimal import Decimal

class LedgerEntry(BaseModel):
    """
    MIRA-compliant double-entry ledger record.
    """
    entry_id: str
    transaction_id: str
    account_code: str # e.g. 1001-CASH, 2001-GST-PAYABLE
    debit: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")
    tax_type: Literal["GGST", "TGST", "NONE"] = "NONE"
    tax_rate: Decimal = Decimal("0.00")
    description: str
    timestamp: datetime = datetime.now(UTC)

class FinancialTransaction(BaseModel):
    transaction_id: str
    amount_base: Decimal
    amount_tax: Decimal
    amount_total: Decimal
    tax_type: str
    status: str = "PENDING"
    entries: List[LedgerEntry] = []

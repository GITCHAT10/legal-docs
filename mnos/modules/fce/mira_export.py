import json
import hashlib
from typing import Dict, Any
from sqlalchemy.orm import Session
from mnos.modules.fce.models import Invoice

def export_mira_json(invoice: Invoice) -> Dict[str, Any]:
    """
    Generates a SHA-256 hash-verified JSON payload for MIRAconnect.
    """
    payload = {
        "invoice_number": invoice.invoice_number,
        "total_amount": invoice.total_amount,
        "tax_summary": invoice.tax_summary,
        "created_at": invoice.created_at.isoformat(),
        "trace_id": invoice.trace_id,
        "tenant_id": invoice.tenant_id
    }

    # Generate verification hash
    payload_str = json.dumps(payload, sort_keys=True)
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    return {
        "mira_payload": payload,
        "verification_hash": payload_hash,
        "standard": "MIRA-EOS-2026"
    }

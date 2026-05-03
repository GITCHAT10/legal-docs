import uuid
from datetime import datetime, UTC

def get_mac_eos_booking_create(tenant):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "MAC_EOS.BOOKING.CREATE",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "MAC_EOS" },
        "actor": { "id": "agent_007", "role": "ADMIN", "device_id": "D-SALA-1" },
        "context": { "tenant": tenant },
        "payload": { "booking_id": "B-101", "base_amount": 1000.00 },
        "proof": {},
        "metadata": { "schema_version": "1.1" }
    }

def get_upos_sale_complete(tenant):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "UPOS.SALE.COMPLETE",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "UPOS" },
        "actor": { "id": "merchant_01", "role": "MERCHANT", "device_id": "POS-SALA-1" },
        "context": { "tenant": tenant },
        "payload": { "transaction_id": "TXN-202", "total_amount": 1287.00, "currency": "USD" },
        "proof": { "shadow_chain_ref": "SH-PREV-01", "orca_validation": {"validated": True} },
        "metadata": { "schema_version": "1.1" }
    }

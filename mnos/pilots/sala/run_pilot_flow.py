from mnos.pilots.sala.staging_seed import SALA_PILOT_CONFIG
from mnos.pilots.sala.sample_events.events import get_mac_eos_booking_create, get_upos_sale_complete
from mnos.core.fce.settlement_guard import SettlementGuard
from mnos.core.shadow.ledger import ShadowLedger

def run_pilot():
    print("Starting SALA Pilot Flow...")
    tenant = SALA_PILOT_CONFIG
    ledger = ShadowLedger()
    guard = SettlementGuard(ledger)

    # 1. MAC_EOS Booking
    booking_event = get_mac_eos_booking_create(tenant)
    # Booking isn't a settlement, but should pass schema validation
    # (In a real system it would go through Gateway)

    # 2. UPOS Sale Settlement
    sale_event = get_upos_sale_complete(tenant)
    status, msg = guard.validate_settlement(sale_event)

    return {
        "booking_event": booking_event,
        "sale_event": sale_event,
        "settlement_status": status,
        "ledger_size": len(ledger.chain)
    }

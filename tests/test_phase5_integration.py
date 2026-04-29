import os
import sys
import shutil
from decimal import Decimal
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.fce.service import FCESovereignService
from mnos.core.fce.wallet import FceWalletService
from mnos.exec.upos.engine import UPOSEngine
from mnos.modules.aqua.engine import AquaDispatchEngine
from mnos.modules.menuorder.engine import MenuOrderEngine
from mnos.modules.marketplace.engine import MarketplaceEngine
from mnos.modules.credit.service import CreditRiskEngine
from mnos.modules.journey.orchestrator import JourneyOrchestrator

def run_phase5_verification():
    print("🇲🇻 PHASE 5: NATIONAL JOURNEY ORCHESTRATION VERIFICATION")
    print("-" * 60)

    # 0. Setup Environment
    for p in ["mnos/core/shadow/storage_p5", "mnos/core/fce/storage_p5"]:
        if os.path.exists(p): shutil.rmtree(p)

    shadow = ShadowSovereignLedger(storage_path="mnos/core/shadow/storage_p5")
    events = DistributedEventBus()
    fce_rule = FCESovereignService()
    wallet = FceWalletService(shadow, events, storage_path="mnos/core/fce/storage_p5")

    # Authorize SYSTEM context
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "SYSTEM", "actor": {"identity_id": "SYSTEM", "role": "admin"}})

    # Instantiate Module Engines
    upos = UPOSEngine(fce_rule, shadow, events)
    aqua = AquaDispatchEngine(wallet, shadow, events)
    menu = MenuOrderEngine(upos, wallet, shadow, events, qr_key="test-key")
    market = MarketplaceEngine(wallet, shadow, events)
    credit = CreditRiskEngine(wallet, shadow)
    journey = JourneyOrchestrator(wallet, shadow, events, aqua, menu, market)

    customer_id = "tourist-001"
    merchant_id = "maafushi-vendor-01"
    trace_id = "tr-p5-journey-001"

    # 1. JOURNEY START: Escrow Deposit
    print("[1] Airport Arrival: Starting Journey...")
    journey_id = journey.start_journey(customer_id, deposit_mvr=1500.0, trace_id=trace_id)
    print(f"    ✔ Journey Initialized: {journey_id}")

    # 2. AQUA: Dispatch Boat to Island
    print("[2] AQUA: Dispatching Speedboat...")
    trip = aqua.match_and_assign({"from": "Airport", "to": "Maafushi"}, pax=2, booking_id="bk-123", trace_id=trace_id)
    print(f"    ✔ Trip Assigned: {trip['vessel_id']} (ETA: {trip['eta_min']}m)")

    # 3. MENUORDER: Table Scan & Order
    print("[3] MENUORDER: Ordering Lunch at Island...")
    session = menu.validate_table_qr({"v": merchant_id, "t": "TABLE-04", "sig": "MOCK"})
    order = menu.submit_table_order(session, [{"sku": "fish-curry", "price": 120.0, "qty": 1}], trace_id=trace_id)
    # Total: 120 + 12 (SC) = 132. 132 * 1.08 = 142.56
    print(f"    ✔ Table Order Placed: {order['order_id']} (Total: {order['pricing']['total']} MVR)")

    # 4. FCE SETTLEMENT: Webhook Confirmation
    print("[4] FCE: Processing Verified Bank Webhook...")
    # BML Webhook simulation
    verified_event = {
        "provider": "bml",
        "transaction_id": "P5-TX-888",
        "invoice_id": order["order_id"],
        "merchant_id": merchant_id,
        "amount_mvr": 142.56
    }
    res = wallet.record_verified_payment(verified_event, trace_id=trace_id)
    print(f"    ✔ Merchant Credited: {res['net_credit']} MVR (1% Fee Deducted)")

    # 5. CREDIT: Emergency Tab Check
    print("[5] CREDIT: Risk Engine Check for High-Trust Activity...")
    risk_res = credit.check_transaction(customer_id, merchant_id, amount_mvr=250.0)
    print(f"    ✔ Credit Check: {'APPROVED' if risk_res['approved'] else 'DENIED'} (Trust Score: {risk_res['trust_score']})")

    # 6. SHADOW AUDIT: Continuity Check
    print("[6] SHADOW: Verifying Forensic Chain...")
    assert shadow.verify_integrity() == True
    print(f"    ✔ Chain Length: {len(shadow.chain)}")
    # Journey start, Trip assigned, Order created, Payment confirmed
    assert len(shadow.chain) >= 4

    print("-" * 60)
    print("✅ PHASE 5 NATIONAL ORCHESTRATION VERIFIED")

if __name__ == "__main__":
    run_phase5_verification()

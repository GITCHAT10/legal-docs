import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest, PricingContext
from mnos.modules.imoxon.supply.engine.router import SupplyRouter, SupplyRequest
from mnos.modules.imoxon.supply.engine.inventory import AllotmentEngine
from mnos.modules.imoxon.supply.integration.hooks import SupplyEXMAILBridge, AsyncEmailQueue
from mnos.modules.imoxon.supply.models.contract import VendorContract, Base
from mnos.modules.imoxon.supply.models.allotment import AllotmentBlock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        # Create outreach_tracker table for tests as it is not in Base.metadata (yet)
        from sqlalchemy import text
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS outreach_tracker (
                email VARCHAR(255) PRIMARY KEY,
                company VARCHAR(255),
                region VARCHAR(50),
                country VARCHAR(50),
                agent_type VARCHAR(50),
                priority_tier VARCHAR(10),
                contact_role VARCHAR(50),
                status VARCHAR(50) DEFAULT 'not-contacted',
                trigger_segment VARCHAR(50),
                last_contact TIMESTAMPTZ,
                notes TEXT
            )
        """))
        yield session

@pytest.mark.asyncio
async def test_full_supply_to_pricing_pipeline(db_session):
    # 1. Setup Allotment
    allotment_engine = AllotmentEngine(db_session)
    block = AllotmentBlock(
        block_id="block_01",
        contract_id="contract_01",
        start_date=date(2024, 5, 20),
        end_date=date(2024, 5, 30),
        total_units=10,
        reserved_units=0
    )
    db_session.add(block)
    await db_session.commit()

    # 2. Supply Resolution
    router = SupplyRouter(allotment_engine)
    supply_req = SupplyRequest(
        product_type="accommodation",
        dates=[date(2024, 5, 22)],
        units=1
    )
    supply_resp = await router.resolve(supply_req)

    assert supply_resp.contract_id == "contract_01"
    assert supply_resp.trigger_hint == "volume" # 8/10 units remaining (mocked stub returns 8)

    # 3. Pricing Calculation
    pricing_engine = PricingEngine()
    pricing_req = PricingRequest(
        net_amount=supply_resp.net_amount,
        product_type=supply_resp.product_type,
        context=PricingContext(
            allotment_pct=80.0, # High allotment -> volume discount
            trigger="volume_push"
        )
    )
    price_resp = pricing_engine.calculate(pricing_req)

    # Assertions
    # Base=145, margin=15% (18% - 3% discount) = 21.75 -> sell=166.75
    # SC=16.68, TGST=31.18 -> Gross=214.61
    assert price_resp.waterfall.margin_pct == 0.15
    assert price_resp.final_gross == Decimal("214.61")
    assert price_resp.tax.tax_type == "TOURISM"

@pytest.mark.asyncio
async def test_urgency_pricing_and_bridge(db_session):
    allotment_engine = AllotmentEngine(db_session)
    # Mocking SupplyRouter.resolve behaviors for urgency
    queue = AsyncEmailQueue()
    bridge = SupplyEXMAILBridge(queue)

    from mnos.modules.imoxon.supply.engine.router import SupplyResponse
    supply_resp = SupplyResponse(
        contract_id="contract_01",
        net_amount=Decimal("200.00"),
        product_type="accommodation",
        tax_type="TOURISM",
        availability_pct=10.0,
        trigger_hint="urgency"
    )

    # Trigger bridge
    await bridge.on_inventory_event("trace_123", supply_resp)
    assert len(queue.queue) == 1
    assert queue.queue[0].trigger == "low_allotment"

    # Pricing for urgency
    pricing_engine = PricingEngine()
    pricing_req = PricingRequest(
        net_amount=supply_resp.net_amount,
        product_type=supply_resp.product_type,
        context=PricingContext(allotment_pct=10.0) # < 20% -> +5% premium
    )
    price_resp = pricing_engine.calculate(pricing_req)

    # Base=200, margin=23% (18% + 5% premium) = 46 -> sell=246
    assert price_resp.waterfall.margin_pct == 0.23
    assert price_resp.waterfall.sell_price == Decimal("246.00")

def test_new_market_segments():
    from mnos.modules.exmail.core.config import NEW_TRIGGER_SEGMENTS
    assert "us_luxury" in NEW_TRIGGER_SEGMENTS
    assert "latam_honeymoon" in NEW_TRIGGER_SEGMENTS
    assert "asia_fast" in NEW_TRIGGER_SEGMENTS

    us_config = NEW_TRIGGER_SEGMENTS["us_luxury"]
    assert us_config["priority"] == "A"
    assert us_config["avg_booking_value"] == 4500

@pytest.mark.asyncio
async def test_contact_attribution(db_session):
    from sqlalchemy import text
    import pandas as pd
    df = pd.read_csv("new_contacts_validated.csv")
    for _, row in df.iterrows():
        await db_session.execute(text("""
            INSERT OR REPLACE INTO outreach_tracker
            (email, company, region, country, agent_type, priority_tier, contact_role, status, trigger_segment)
            VALUES (:email, :company, :region, :country, :agent_type, :priority_tier, :contact_role, :status, :trigger_segment)
        """), row.to_dict())
    await db_session.commit()

    result = await db_session.execute(text("SELECT COUNT(*) FROM outreach_tracker"))
    count = result.scalar()
    assert count == 505

    res = await db_session.execute(text("SELECT trigger_segment FROM outreach_tracker WHERE region='USA' LIMIT 1"))
    assert res.scalar() == "us_luxury"

@pytest.mark.asyncio
async def test_aidas_global_dominance_pack():
    # 1. Guest Intel Vault
    from prestige.security.guest_vault import GuestIntelVault
    vault = GuestIntelVault()
    intel = {"net_worth": "Ultra", "intent": "Private Yacht", "privacy_required": True}
    encrypted = vault.encrypt_guest_intel(intel)
    decrypted = vault.decrypt_guest_intel(encrypted)
    assert decrypted["net_worth"] == "Ultra"

    score = vault.score_guest_value(decrypted)
    # 1.0 + 0.3 + 0.2 + 0.15 = 1.65
    assert float(score) == 1.65

    # 2. Vision Swarm (Mocked)
    from prestige.content.vision_swarm import VisionSwarm, ContentRequest
    swarm = VisionSwarm()
    req = ContentRequest(
        target_region="GCC",
        guest_archetype="Ultra-Luxury",
        usp_focus="Privacy",
        resort_id="PRESTIGE_01",
        trace_id="TR-789"
    )
    asset_path = await swarm.generate_personalized_asset(req)
    assert "TR-789_GCC.mp4" in asset_path

    # 3. Regional Pitch Bot
    from prestige.sales.regional_pitch import RegionalPitchBot
    bot = RegionalPitchBot()
    pitch = bot.generate_closing_pitch("GCC", decrypted)
    assert "We are honored" in pitch
    assert "Private Seaplane" in pitch

    # 4. Competitor Intercept
    from prestige.intel.competitor_monitor import CompetitorInterceptEngine
    intercept = CompetitorInterceptEngine()
    intel_data = await intercept.monitor_competitor_intel("North_Male")
    assert intel_data["atoll"] == "North_Male"
    assert "intercept_opportunity" in intel_data

    # 5. Geo Intelligence Router (Mocked)
    from prestige.router.geo_intelligence import GeoIntelligenceRouter
    router = GeoIntelligenceRouter()
    gcc_config = router.detect_region_from_ip("5.1.1.1")
    assert gcc_config["region"] == "GCC"
    assert gcc_config["pricing_variant"] == "premium_fast"

@pytest.mark.asyncio
async def test_gds_orchestrator():
    from mnos.modules.imoxon.gds.orchestrator import GDSOrchestrator, GDSProvider
    from mnos.modules.imoxon.pricing.engine import PricingEngine

    pricing = PricingEngine()
    gds = GDSOrchestrator(pricing)

    # Search Amadeus (Default for Europe)
    results = await gds.search_flights("LHR", "MLE", ["2024-12-20"])
    assert len(results) == 1
    assert results[0]["provider"] == "AMADEUS"
    assert results[0]["currency"] == "MVR"
    assert results[0]["maldives_compliance"]["pdpa_ready"] is True

    # Search Sabre (Default for Americas)
    results_us = await gds.search_flights("JFK", "MLE", ["2024-12-20"])
    assert results_us[0]["provider"] == "SABRE"

    # Phone validation (+960 + 7 or 9 digits)
    assert gds.validate_phone("+960123456789") is True
    assert gds.validate_phone("+1234567890") is False

@pytest.mark.asyncio
async def test_multi_channel_signal_engine():
    from mnos.modules.imoxon.signal.engine import SignalEvent, BayesianIntentScorer, ThrottleManager
    from datetime import datetime

    # 1. Scoring
    scorer = BayesianIntentScorer()
    history = [
        SignalEvent(contact_id="c1", channel="whatsapp", event_type="reply", payload={}, occurred_at=datetime.utcnow()),
        SignalEvent(contact_id="c1", channel="email", event_type="click", payload={}, occurred_at=datetime.utcnow())
    ]
    score = scorer.calculate_score(history)
    # alpha=2, beta=5. evidence = 0.35 + 0.14 = 0.49. alpha_post = 2 + 4.9 = 6.9, beta_post = 5 + 2 = 7. 6.9 / 13.9 = 0.496
    assert score == 0.496

    # 2. Throttle
    throttle = ThrottleManager()
    acc = "acc_01"
    for _ in range(20):
        assert throttle.check_throttle(acc, "whatsapp") is True
        throttle.record_activity(acc, "whatsapp")

    assert throttle.check_throttle(acc, "whatsapp") is False

@pytest.mark.asyncio
async def test_honeymoon_revenue_forecasting():
    from mnos.modules.exmail.monitoring.forecaster import HoneymoonRevenueForecaster
    forecaster = HoneymoonRevenueForecaster()
    # List size 100, segment luxury
    # open 0.54 * click 0.28 * conv 0.18 = 0.027216 -> 2.72 bookings
    # mean AOV 195,000 -> 2.72 * 195,000 = 530,712 MVR
    res = forecaster.project_revenue(100, "eu_honeymoon_luxury")
    assert res["expected_bookings"] == 2.72
    assert res["projected_revenue_mean"] > 400000

@pytest.mark.asyncio
async def test_canary_selection_reproducibility():
    from mnos.modules.exmail.core.canary import CanarySelector
    selector = CanarySelector(seed="TEST_SEED")
    agents = [{"email": f"agent{i}@test.com"} for i in range(100)]

    selection1 = selector.select_agents(agents, 0.10)
    selection2 = selector.select_agents(agents, 0.10)

    assert len(selection1) == 10
    assert selection1 == selection2

def test_retail_tax_logic():
    engine = PricingEngine()
    req = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="retail"
    )
    resp = engine.calculate(req)
    # net=100, margin=10% -> sell=110
    # retail rule: SC=0, GST=8% -> 110 * 0.08 = 8.80 -> gross=118.80
    assert resp.tax.service_charge == Decimal("0.00")
    assert resp.tax.tgst == Decimal("8.80")
    assert resp.final_gross == Decimal("118.80")

@pytest.mark.asyncio
async def test_dual_currency_and_maldivian_rule():
    from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest, PricingContext
    engine = PricingEngine()

    # 1. Foreign User (USD Display)
    req_foreign = PricingRequest(
        net_amount=Decimal("1000.00"),
        product_type="accommodation",
        context=PricingContext(currency="USD")
    )
    resp_foreign = engine.calculate(req_foreign, user_nationality="Foreign")
    assert resp_foreign.currency == "USD"
    # Base 1000 + 18% margin = 1180
    # SC 10% = 118, Subtotal = 1298
    # TGST 17% of 1298 = 220.66
    # Total USD = 1518.66
    assert resp_foreign.final_gross == Decimal("1518.66")
    assert resp_foreign.tax.tgst == Decimal("220.66")

    # 2. Maldivian User (Force MVR)
    req_local = PricingRequest(
        net_amount=Decimal("1000.00"),
        product_type="accommodation",
        context=PricingContext(currency="USD") # Input still USD
    )
    resp_local = engine.calculate(req_local, user_nationality="Maldivian")
    assert resp_local.currency == "MVR"
    # Rate = 15.42 * 1.01 = 15.57 (quantized to 0.01)
    # 1518.66 * 15.57 = 23645.5362 -> 23645.54 (quantized to 0.01)
    assert resp_local.final_gross == Decimal("23645.54")

@pytest.mark.asyncio
async def test_fx_compliance_buffer():
    from mnos.modules.finance.fx_compliance import FXComplianceEngine
    fx = FXComplianceEngine()

    # MMA 15.42. 1% buffer = 15.5742 -> 15.57 (quantized to 0.01)
    rate = fx.get_compliant_fx_rate(Decimal("15.42"))
    assert rate == Decimal("15.57")

    # Test bounds
    # Lower bound (MMA * 0.98) = 15.1116 -> 15.12
    # Upper bound (MMA * 1.02) = 15.7284 -> 15.72
    assert rate >= Decimal("15.42") * Decimal("0.98")
    assert rate <= Decimal("15.42") * Decimal("1.02")

@pytest.mark.asyncio
async def test_full_booking_lifecycle(db_session):
    from mnos.modules.imoxon.booking.manager import BookingManager, BookingState
    from mnos.modules.imoxon.core.engine import ImoxonCore
    from mnos.modules.finance.fce import FCEEngine
    from mnos.modules.finance.fx_compliance import FXComplianceEngine
    from mnos.modules.events.bus import DistributedEventBus
    from mnos.modules.shadow.ledger import ShadowLedger
    from mnos.shared.execution_guard import ExecutionGuard
    from prestige.services.inventory.realtime_ledger import RealtimeInventoryLedger

    # 1. Setup Environment
    shadow = ShadowLedger()
    events = DistributedEventBus()
    fce = FCEEngine()
    class MockPolicy:
        def validate_action(self, at, ctx): return True, "OK"
    guard = ExecutionGuard(None, MockPolicy(), fce, shadow, events)
    core = ImoxonCore(guard, fce, shadow, events)
    inventory = RealtimeInventoryLedger(core)
    manager = BookingManager(core, inventory)

    actor = {"identity_id": "AGENT_01", "role": "agent", "device_id": "DEV_01"}

    # 2. Step 1: QUOTE
    from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest
    pricing_engine = PricingEngine(fce, FXComplianceEngine())
    req = PricingRequest(net_amount=Decimal("5000.00"), product_type="accommodation")
    pricing_resp = pricing_engine.calculate(req)

    with guard.sovereign_context(actor):
        booking = manager.create_quote(actor, pricing_resp)
        assert booking["state"] == BookingState.QUOTE
        booking_id = booking["id"]

        # 3. Step 2: CONFIRM
        manager.confirm_booking(actor, booking_id, "VILLA_01", "2024-12-20", 1)
        assert manager.bookings[booking_id]["state"] == BookingState.CONFIRMED

        # 4. Step 3: PAYMENT
        manager.record_payment(actor, booking_id, "WIRE-TRANS-999")
        assert manager.bookings[booking_id]["state"] == BookingState.PAID

        # 5. Step 4: INVOICE (Final)
        final_booking = manager.lock_and_invoice(actor, booking_id)
        assert final_booking["state"] == BookingState.INVOICED
        assert "invoice" in final_booking
        assert final_booking["invoice"]["total_mvr"] > 0
        assert final_booking["invoice"]["tgst_usd_extracted"] > 0

    # 6. Verify SHADOW Audit Chain
    assert len(shadow.chain) >= 4
    events_in_audit = [b["event_type"] for b in shadow.chain]
    assert "booking.invoiced.completed" in events_in_audit

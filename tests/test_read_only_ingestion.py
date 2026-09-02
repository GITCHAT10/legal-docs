import pytest

from mnos.modules.ingestion import ReadOnlyIngestionEngine


def axiom_record(record_id="AX-1"):
    return {
        "record_id": record_id,
        "business_date": "2026-09-02",
        "outlet_id": "SALA-COCO",
        "net_amount": 100.0,
        "tax_amount": 17.0,
    }


def sala_record(record_id="PMS-1"):
    return {
        "record_id": record_id,
        "business_date": "2026-09-02",
        "property_id": "SALA-OMADHOO",
        "room_revenue": 1200.0,
        "occupancy": 0.75,
    }


def test_axiom_and_sala_exports_are_accepted_read_only():
    engine = ReadOnlyIngestionEngine()
    assert engine.ingest(tenant_id="MIG", source="AXIOM_FNB", cursor=1, records=[axiom_record()])["accepted"] == 1
    assert engine.ingest(tenant_id="MIG", source="SALA_PMS", cursor=1, records=[sala_record()])["accepted"] == 1
    assert all(event["mode"] == "READ_ONLY_EXPORT" for event in engine.read_events(tenant_id="MIG"))


def test_ingestion_is_tenant_isolated_and_returns_copies():
    engine = ReadOnlyIngestionEngine()
    engine.ingest(tenant_id="MIG", source="AXIOM_FNB", cursor=1, records=[axiom_record()])
    engine.ingest(tenant_id="OTHER", source="AXIOM_FNB", cursor=1, records=[axiom_record()])
    mig_events = engine.read_events(tenant_id="MIG")
    assert len(mig_events) == 1
    mig_events[0]["payload"]["net_amount"] = 999
    assert engine.read_events(tenant_id="MIG")[0]["payload"]["net_amount"] == 100.0


def test_duplicate_is_idempotent_and_stale_cursor_fails_closed():
    engine = ReadOnlyIngestionEngine()
    engine.ingest(tenant_id="MIG", source="SALA_PMS", cursor=5, records=[sala_record()])
    result = engine.ingest(tenant_id="MIG", source="SALA_PMS", cursor=5, records=[sala_record()])
    assert result == {"accepted": 0, "duplicates": 1, "cursor": 5}
    with pytest.raises(ValueError, match="STALE_CURSOR"):
        engine.ingest(tenant_id="MIG", source="SALA_PMS", cursor=4, records=[])


def test_invalid_source_or_schema_is_rejected_atomically():
    engine = ReadOnlyIngestionEngine()
    with pytest.raises(ValueError, match="SOURCE_NOT_ALLOWED"):
        engine.ingest(tenant_id="MIG", source="UNKNOWN", cursor=1, records=[])
    with pytest.raises(ValueError, match="MISSING_REQUIRED_FIELDS"):
        engine.ingest(tenant_id="MIG", source="AXIOM_FNB", cursor=1, records=[{"record_id": "bad"}])
    assert engine.read_events(tenant_id="MIG") == ()

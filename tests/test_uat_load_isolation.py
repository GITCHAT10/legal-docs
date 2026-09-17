from concurrent.futures import ThreadPoolExecutor

from mnos.modules.ingestion import ReadOnlyIngestionEngine


def record(index: int) -> dict:
    return {
        "record_id": f"AX-{index}",
        "business_date": "2026-09-03",
        "outlet_id": "SALA-COCO",
        "net_amount": float(index),
        "tax_amount": float(index) * 0.17,
    }


def test_parallel_tenant_load_remains_isolated_and_complete():
    engine = ReadOnlyIngestionEngine()

    def ingest(tenant: str, start: int) -> None:
        engine.ingest(
            tenant_id=tenant,
            source="AXIOM_FNB",
            cursor=1,
            records=[record(index) for index in range(start, start + 100)],
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(ingest, "MIG", 100),
            pool.submit(ingest, "MIG", 200),
            pool.submit(ingest, "OTHER", 100),
            pool.submit(ingest, "OTHER", 200),
        ]
        for future in futures:
            future.result()

    assert len(engine.read_events(tenant_id="MIG")) == 200
    assert len(engine.read_events(tenant_id="OTHER")) == 200
    assert {event["tenant_id"] for event in engine.read_events(tenant_id="MIG")} == {"MIG"}

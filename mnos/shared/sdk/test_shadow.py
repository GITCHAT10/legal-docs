import pytest
from mnos.shared.sdk.mnos_client import ShadowClient

def test_shadow_hash_chain():
    client = ShadowClient()
    trace_id = "test_trace_1"
    payload1 = {"action": "start"}
    payload2 = {"action": "stop"}

    hash1 = client.commit(payload1, trace_id)
    hash2 = client.commit(payload2, trace_id)

    assert hash1 != hash2
    assert len(hash1) == 64
    assert client.last_hash == hash2

def test_shadow_reproducibility():
    client1 = ShadowClient()
    client2 = ShadowClient()
    trace_id = "trace_x"
    payload = {"data": 123}

    h1 = client1.commit(payload, trace_id)
    h2 = client2.commit(payload, trace_id)

    assert h1 == h2

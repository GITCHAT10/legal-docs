import pytest
from mnos.core.fce.idempotency import calculate_idempotency_key

def test_idempotency_consistency():
    key1 = calculate_idempotency_key("TIN123", "SALE", "TXN1", 100.0, "USD", "SHADOW1")
    key2 = calculate_idempotency_key("TIN123", "SALE", "TXN1", 100.0, "USD", "SHADOW1")
    assert key1 == key2

def test_idempotency_uniqueness():
    key1 = calculate_idempotency_key("TIN123", "SALE", "TXN1", 100.0, "USD", "SHADOW1")
    key2 = calculate_idempotency_key("TIN123", "SALE", "TXN1", 100.01, "USD", "SHADOW1")
    assert key1 != key2

import pytest
from mnos.modules.pms.adapters.placeholders import OperaAdapter, MewsAdapter, CloudbedsAdapter

def test_opera_normalization():
    adapter = OperaAdapter()
    raw = {
        "res_id": "OP-999", "hotel_code": "MIG-01", "arrival": "2024-10-10",
        "departure": "2024-10-15", "room_type": "DELUXE", "rate_amount": 1200.0,
        "currency": "USD", "res_channel": "GDS"
    }
    canonical = adapter.normalize(raw)
    assert canonical.source_system == "OPERA"
    assert canonical.base_rate == 1200.0
    assert canonical.arrival_date.isoformat() == "2024-10-10"

def test_mews_normalization():
    adapter = MewsAdapter()
    raw = {
        "Id": "MW-111", "EnterpriseId": "ENT-01", "StartUtc": "2024-11-01T14:00:00Z",
        "EndUtc": "2024-11-05T11:00:00Z", "SpaceType": "VILLA", "Rate": 2500.0
    }
    canonical = adapter.normalize(raw)
    assert canonical.source_system == "MEWS"
    assert canonical.base_rate == 2500.0
    assert canonical.arrival_date.isoformat() == "2024-11-01"

def test_cloudbeds_normalization():
    adapter = CloudbedsAdapter()
    raw = {
        "reservationID": "CB-222", "propertyID": "PROP-A", "checkin": "2024-12-20",
        "checkout": "2024-12-25", "roomTypeName": "BUNGALOW", "grandTotal": 3000.0
    }
    canonical = adapter.normalize(raw)
    assert canonical.source_system == "CLOUDBEDS"
    assert canonical.base_rate == 3000.0

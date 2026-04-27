import pytest
from fastapi.testclient import TestClient
from main import app, airmovie_engine, airmovie_sync, shadow_core, identity_core, guard

client = TestClient(app)

@pytest.fixture
def setup_airmovie():
    # Setup test content
    airmovie_engine.add_content({
        "id": "test-movie-1",
        "title": "Sovereign Seas",
        "room_binding": None
    })

    # Create test identity
    actor_id = identity_core.create_profile({
        "full_name": "Test Guest",
        "profile_type": "guest"
    })
    device_id = "test-device-1"
    identity_core.devices[device_id] = {"identity_id": actor_id}

    return {"actor_id": actor_id, "device_id": device_id}

def test_airmovie_full_flow(setup_airmovie):
    actor_id = setup_airmovie["actor_id"]
    device_id = setup_airmovie["device_id"]

    # 1. Access Catalog
    response = client.get(
        "/imoxon/airmovie/catalog",
        headers={
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
            "X-BYPASS-GATEWAY": "true"
        }
    )
    assert response.status_code == 200
    catalog = response.json()
    assert any(m["title"] == "Sovereign Seas" for m in catalog)

    # 2. Start Playback
    response = client.post(
        "/imoxon/airmovie/play",
        json={
            "content_id": "test-movie-1",
            "device_hash": "hash123",
            "room_id": "V402"
        },
        headers={
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
            "X-BYPASS-GATEWAY": "true"
        }
    )
    assert response.status_code == 200
    play_data = response.json()
    assert "session_id" in play_data
    assert "manifest_url" in play_data
    assert "watermark" in play_data

    # 3. Verify Offline Log Queued (check DB indirectly via sync)
    response = client.post(
        "/imoxon/airmovie/sync",
        headers={
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
            "X-BYPASS-GATEWAY": "true"
        }
    )
    assert response.status_code == 200
    assert response.json()["synced_logs"] >= 1

    # 4. Verify SHADOW Audit
    audit_trail = [e for e in shadow_core.chain if e["event_type"] == "airmovie.playback.started"]
    assert len(audit_trail) >= 1
    assert audit_trail[-1]["actor_id"] == actor_id

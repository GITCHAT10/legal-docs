import unittest
from mnos.core.comms.hubble_i.service import hubble_i
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
import json
import hmac
import hashlib

class TestHubbleOffGrid(unittest.TestCase):
    def setUp(self):
        self.ctx_payload = {"device_id": "MIG-HUBBLE-I-2026-INIT"}
        from mnos.config import config
        sig = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        self.ctx = self.ctx_payload.copy()
        self.ctx["signature"] = sig

    def test_hubble_beacon_initiation(self):
        # 1. Initiate beacon
        asset_id = "AQUA-001"
        data = {"geo_coords": [4.17, 73.50], "health": "GOOD"}
        beacon = hubble_i.initiate_satellite_beacon(asset_id, data)
        self.assertEqual(beacon["status"], "BEACON_ACTIVE")
        self.assertEqual(beacon["asset_id"], "AQUA-001")

    def test_execution_guard_hubble_scope(self):
        # 2. Guarded Allowed
        payload = {"geo_coords": [4.17, 73.50]}
        res = guard.execute_sovereign_action(
            "hubble.location_update",
            payload,
            self.ctx,
            lambda p: p
        )
        self.assertEqual(res["geo_coords"], [4.17, 73.50])

    def test_execution_guard_hubble_blocked(self):
        # 3. Guarded Blocked (Remote Admin)
        payload = {"command": "reboot"}
        with self.assertRaises(RuntimeError) as cm:
            guard.execute_sovereign_action(
                "hubble.remote_admin",
                payload,
                self.ctx,
                lambda p: p
            )
        self.assertIn("OFF_GRID_VIOLATION", str(cm.exception))

if __name__ == "__main__":
    unittest.main()

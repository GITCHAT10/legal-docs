import unittest
import json
import hashlib
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import in_sovereign_context

class TestShadowChronologyIntegrity(unittest.TestCase):
    def setUp(self):
        # Reset shadow for clean state
        shadow.chain = []
        shadow._seed_ledger()
        self.token = in_sovereign_context.set(True)

    def tearDown(self):
        in_sovereign_context.reset(self.token)

    def test_1_timestamp_tamper(self):
        shadow.commit("TEST_EVENT", {"data": "test"})
        original_ts = shadow.chain[1]["timestamp"]
        shadow.chain[1]["timestamp"] = "2026-04-23T10:00:00Z"
        self.assertFalse(shadow.verify_integrity(), "Integrity should fail on timestamp tamper")
        shadow.chain[1]["timestamp"] = original_ts
        self.assertTrue(shadow.verify_integrity())
        print("✔ chronology immutable")

    def test_2_actor_id_tamper(self):
        # We simulate actor_id if supported
        entry = {
            "entry_id": len(shadow.chain),
            "timestamp": "2026-04-23T12:00:00Z",
            "event_type": "ACTOR_EVENT",
            "payload": {},
            "previous_hash": shadow.chain[-1]["hash"],
            "actor_id": "MIG-CEO-01"
        }
        entry["hash"] = shadow._calculate_hash(entry)
        shadow.chain.append(entry)

        self.assertTrue(shadow.verify_integrity())
        shadow.chain[-1]["actor_id"] = "EVIL-ACTOR"
        self.assertFalse(shadow.verify_integrity(), "Integrity should fail on actor_id tamper")
        print("✔ actor bound")

    def test_3_objective_code_tamper(self):
        entry = {
            "entry_id": len(shadow.chain),
            "timestamp": "2026-04-23T12:05:00Z",
            "event_type": "OBJ_EVENT",
            "payload": {},
            "previous_hash": shadow.chain[-1]["hash"],
            "objective_code": "SECURE_PERIMETER"
        }
        entry["hash"] = shadow._calculate_hash(entry)
        shadow.chain.append(entry)

        self.assertTrue(shadow.verify_integrity())
        shadow.chain[-1]["objective_code"] = "OPEN_GATES"
        self.assertFalse(shadow.verify_integrity(), "Integrity should fail on objective_code tamper")
        print("✔ objective bound")

    def test_4_payload_tamper(self):
        shadow.commit("TEST_EVENT", {"data": "safe"})
        shadow.chain[-1]["payload"] = {"data": "malicious"}
        self.assertFalse(shadow.verify_integrity(), "Integrity should fail on payload tamper")

    def test_5_previous_hash_tamper(self):
        shadow.commit("EVENT_1", {})
        shadow.commit("EVENT_2", {})
        shadow.chain[-1]["previous_hash"] = "0" * 64
        self.assertFalse(shadow.verify_integrity(), "Integrity should fail on previous_hash tamper")

    def test_6_genesis_block_tamper(self):
        shadow.chain[0]["payload"] = {"tamper": "genesis"}
        self.assertFalse(shadow.verify_integrity(), "Integrity should fail on genesis tamper")
        print("✔ genesis secured")

    def test_7_valid_chain(self):
        shadow.commit("VALID_1", {"v": 1})
        shadow.commit("VALID_2", {"v": 2})
        self.assertTrue(shadow.verify_integrity(), "Valid chain should pass")

    def test_8_deterministic_hash(self):
        entry = {
            "entry_id": 99,
            "timestamp": "2026-01-01T00:00:00Z",
            "event_type": "DET_EVENT",
            "payload": {"a": 1, "b": 2},
            "previous_hash": "abc"
        }
        h1 = shadow._calculate_hash(entry)
        h2 = shadow._calculate_hash(entry)
        self.assertEqual(h1, h2, "Hash should be deterministic")
        print("✔ deterministic hashing verified")

if __name__ == "__main__":
    unittest.main()

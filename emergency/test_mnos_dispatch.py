import tempfile
import unittest
from pathlib import Path
from emergency.mnos_dispatch import Conflict, EmergencyKernel


class DispatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.kernel = EmergencyKernel(Path(self.tmp.name) / "dispatch.db")
        self.reporter = {"id": "guest", "role": "reporter"}
        self.dispatcher = {"id": "operator", "role": "dispatcher"}
        self.driver = {"id": "boat-1", "role": "responder"}

    def test_idempotent_report_and_guarded_lifecycle(self):
        case = self.kernel.report("Omadhoo", "request-1", self.reporter)
        self.assertEqual(case["id"], self.kernel.report("Omadhoo", "request-1", self.reporter)["id"])
        with self.assertRaises(Conflict):
            self.kernel.advance(case["id"], "OFFERED", 0, self.dispatcher, responder_id="boat-1")
        case = self.kernel.advance(case["id"], "ACKNOWLEDGED", 0, self.dispatcher)
        case = self.kernel.advance(case["id"], "OFFERED", 1, self.dispatcher, responder_id="boat-1")
        with self.assertRaises(PermissionError):
            self.kernel.advance(case["id"], "ACCEPTED", 2, {"id": "other", "role": "responder"})
        case = self.kernel.advance(case["id"], "ACCEPTED", 2, self.driver)
        with self.assertRaises(Conflict):
            self.kernel.advance(case["id"], "EN_ROUTE", 2, self.driver)
        for state in ("EN_ROUTE", "ON_SCENE", "TRANSFER"):
            case = self.kernel.advance(case["id"], state, case["version"], self.driver)
        with self.assertRaises(ValueError):
            self.kernel.advance(case["id"], "HANDOFF", case["version"], {"id": "medic", "role": "clinician"})
        case = self.kernel.advance(case["id"], "HANDOFF", case["version"], {"id": "medic", "role": "clinician"}, facility_id="hospital-1")
        self.assertEqual(self.kernel.advance(case["id"], "CLOSED", case["version"], self.dispatcher)["status"], "CLOSED")
        self.assertEqual(len(self.kernel.history(case["id"])), 9)

    def test_reoffer_and_cancellation(self):
        case = self.kernel.report("Malé", "request-2", self.reporter)
        case = self.kernel.advance(case["id"], "ACKNOWLEDGED", 0, self.dispatcher)
        case = self.kernel.advance(case["id"], "OFFERED", 1, self.dispatcher, responder_id="boat-1")
        case = self.kernel.advance(case["id"], "ACKNOWLEDGED", 2, self.dispatcher, reason="Declined")
        self.assertIsNone(case["assigned_to"])
        with self.assertRaises(ValueError):
            self.kernel.advance(case["id"], "CANCELLED", 3, self.dispatcher)
        self.assertEqual(self.kernel.advance(case["id"], "CANCELLED", 3, self.dispatcher, reason="Duplicate")["status"], "CANCELLED")


if __name__ == "__main__":
    unittest.main()

import unittest
import requests
import time
import subprocess
import os
import signal

class TestDMTE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start Edge Node
        cls.edge_process = subprocess.Popen(["python3", "edge-node/main.py"],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Start Sovereign Backend
        cls.backend_process = subprocess.Popen(["python3", "sovereign-backend/main.py"],
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3) # Wait for servers to start

    @classmethod
    def tearDownClass(cls):
        os.kill(cls.edge_process.pid, signal.SIGTERM)
        os.kill(cls.backend_process.pid, signal.SIGTERM)

    def test_edge_node_compliance(self):
        resp = requests.get("http://localhost:8001/compliance?vessel_id=123")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "CLEARED")

        resp = requests.get("http://localhost:8001/compliance?vessel_id=999")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "BLOCKED")

    def test_edge_node_environment(self):
        resp = requests.get("http://localhost:8001/environment")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("risk", resp.json())

    def test_backend_sync_and_dashboard(self):
        log = {"id": "test-sync-1", "vessel_id": "123", "status": "VERIFIED"}
        resp = requests.post("http://localhost:8002/sync-logs", json=[log])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")

        resp = requests.get("http://localhost:8002/dashboard-data")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["total_dispatches"], 1)

if __name__ == "__main__":
    unittest.main()

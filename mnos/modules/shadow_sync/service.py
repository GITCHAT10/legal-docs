import time
import threading
from typing import Dict, Any

class ShadowSync:
    """
    Shadow-Sync: Air-Gap Cognitive Isolation.
    Mirrors external 'Truth State' (Registry/HMS) into local autonomous cache.
    """
    def __init__(self):
        self.local_registry = {}
        self.local_hms = {}
        self.is_running = False
        self.sync_thread = None

    def start_sync(self):
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            print("[Shadow-Sync] Cognitive Isolation Loop started.")

    def _sync_loop(self):
        while self.is_running:
            try:
                self._mirror_state()
            except Exception as e:
                print(f"[Shadow-Sync] Sync Error: {e}")
            time.sleep(60)

    def _mirror_state(self):
        """Simulate mirroring from external Transport Ministry / HMS APIs."""
        # In production, this would call actual APIs via ORBAN secure tunnel
        print("[Shadow-Sync] Mirroring Registry and HMS state (Local Autonomous Mode)...")

        # Mock data ingestion
        self.local_registry = {
            "AL-SAFAR 2": {"status": "ACTIVE", "mfr_verified": True},
            "MARINA-V1": {"status": "ACTIVE", "mfr_verified": True}
        }
        self.local_hms = {
            "JETTY-A": {"berth_availability": 4, "power_status": "ON"},
            "JETTY-B": {"berth_availability": 2, "power_status": "ON"}
        }
        print("[Shadow-Sync] Local Truth State updated.")

    def get_vessel_status(self, vessel_id: str) -> Dict[str, Any]:
        return self.local_registry.get(vessel_id, {"status": "UNKNOWN", "mfr_verified": False})

shadow_sync = ShadowSync()

import json
from .db import AirMovieDB

class AirMovieSyncEngine:
    def __init__(self, shadow_core, guard):
        self.db = AirMovieDB()
        self.shadow = shadow_core
        self.guard = guard

    def sync_pending_logs(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, payload FROM sync_queue WHERE status = 'pending' AND type = 'log'")
        pending = cursor.fetchall()

        synced_count = 0
        for entry_id, payload_str in pending:
            payload = json.loads(payload_str)
            trace_id = payload.get("trace_id", "SYNC-GEN")

            with self.guard.sovereign_context(trace_id=trace_id):
                # In a real scenario, this would push to a central cloud endpoint
                # Here we simulate by committing to the local shadow ledger as 'synced'
                self.shadow.commit("airmovie.sync.log", "SYSTEM", {
                    "original_event": payload["event"],
                    "session_id": payload.get("session_id"),
                    "status": "CLOUDSYNC_OK"
                })

                cursor.execute("UPDATE sync_queue SET status = 'synced' WHERE id = ?", (entry_id,))
                synced_count += 1

        conn.commit()
        conn.close()
        return synced_count

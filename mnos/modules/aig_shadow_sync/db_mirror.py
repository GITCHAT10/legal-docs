from typing import Dict, Any, List

class DatabaseMirror:
    """
    Local Database (Edge Node):
    Starts as READ-ONLY mirror, promotable to READ-WRITE.
    """
    def __init__(self):
        self.is_primary = False
        self.data: Dict[str, Dict[str, Any]] = {} # Simple table-based storage

    def apply_change(self, event: Dict[str, Any]):
        """Applies cloud CDC changes to local mirror."""
        table = event["table"]
        data = event["data"]
        op = event["operation"]

        if table not in self.data:
            self.data[table] = {}

        record_id = data.get("id")
        if op in ["INSERT", "UPDATE"]:
            self.data[table][record_id] = data
        elif op == "DELETE":
            self.data[table].pop(record_id, None)

    def write_local(self, table: str, data: Dict[str, Any]):
        """Writes to local DB only if it has been promoted to PRIMARY."""
        if not self.is_primary:
            raise RuntimeError("DB_MIRROR: Write denied. Database is in READ-ONLY mirror mode.")

        if table not in self.data:
            self.data[table] = {}

        record_id = data.get("id")
        self.data[table][record_id] = data

        # Track for reconciliation
        from mnos.modules.aig_shadow_sync.service import sync_agent
        sync_agent.queue_local_change({"table": table, "data": data, "operation": "UPSERT"})

    def promote(self):
        """Promotes local DB to READ-WRITE (PRIMARY)."""
        self.is_primary = True
        print("[DB_MIRROR] Local database promoted to PRIMARY.")

    def demote(self):
        """Demotes local DB to READ-ONLY (MIRROR)."""
        self.is_primary = False
        print("[DB_MIRROR] Local database demoted to MIRROR.")

db_mirror = DatabaseMirror()

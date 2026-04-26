import enum
from datetime import datetime, UTC
import uuid

class FailoverMode(enum.Enum):
    STANDARD = "STANDARD"
    LOCAL_TX_ONLY = "LOCAL_TX_ONLY" # 0200 Protocol Active
    RECOVERY = "RECOVERY"

class Protocol0200Failover:
    """
    INIT_0200_FAILOVER_PROTOCOL_ILUVIA
    Implements P0 Failover for local island operations during external link loss.
    """
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.mode = FailoverMode.STANDARD
        self.write_barrier_enabled = False
        self.local_wal = [] # Write-ahead log for local commits

    def activate_protocol_0200(self):
        """
        ENABLE_WRITE_BARRIER, ALLOW_LOCAL_TX_ONLY, DISABLE_EXTERNAL_BANK_CALLS
        """
        self.mode = FailoverMode.LOCAL_TX_ONLY
        self.write_barrier_enabled = True

        event = {
            "protocol": "0200",
            "action": "ACTIVATED",
            "merkle_root_sealed": True,
            "timestamp": datetime.now(UTC).isoformat()
        }
        # Sealed root anchoring in SHADOW
        self.shadow.commit("system.failover.activated", "SYSTEM", event)
        print("🚨 PROTOCOL 0200 ACTIVE: Local Economy Mode Enabled.")

    def execute_failover_tx(self, action_type: str, actor_ctx: dict, func, *args, **kwargs):
        """
        LOCAL_COMMIT_ALLOWED, MARK_PENDING_EXTERNAL
        """
        if self.mode != FailoverMode.LOCAL_TX_ONLY:
             return self.guard.execute_sovereign_action(action_type, actor_ctx, func, *args, **kwargs)

        # Implementation of WRITE_BARRIER: block external-only actions
        external_actions = ["finance.bank.withdraw", "imoxon.global.rfq"]
        if action_type in external_actions:
             raise RuntimeError("FAILOVER ACTIVE: External bank calls disabled.")

        # Local execution allowed for liquidity
        # Logic: QR Payments, POS transactions, Vendor spend
        result = func(*args, **kwargs)

        record = {
            "action": action_type,
            "actor": actor_ctx["identity_id"],
            "result": result,
            "status": "PENDING_EXTERNAL_SYNC",
            "trace_id": uuid.uuid4().hex[:8]
        }
        self.local_wal.append(record)

        # Shadow entry in local WAL
        self.shadow.commit(f"{action_type}.local_commit", actor_ctx["identity_id"], record)
        return result

    def start_recovery(self):
        """
        SYNC_PENDING_TX_TO_IMOXON, RECONCILE_LEDGER
        """
        self.mode = FailoverMode.RECOVERY
        print(f"🔄 RECOVERY STARTED: Replaying {len(self.local_wal)} local transactions...")

        for tx in self.local_wal:
             # Reconcile with main ledger
             self.events.publish("system.recovery.reconcile", tx)

        self.local_wal = []
        self.mode = FailoverMode.STANDARD
        self.write_barrier_enabled = False
        print("✅ RECOVERY COMPLETE: Operations unlocked.")

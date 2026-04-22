import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from mnos.modules.shadow.service import shadow
from mnos.config import config

class SALService:
    """
    Sovereign Audit Log (SAL): Cryptographically signed technical proof of sovereignty.
    """
    def log(self,
            trace_id: str,
            actor_identity: str,
            event_type: str,
            payload: Dict[str, Any],
            intent_score: float = 1.0,
            jurisdiction: str = "MV") -> str:
        """
        Logs a sovereign dimension event and seals it in SHADOW.
        """
        # Directive: Capture the five Sovereign Dimensions
        log_entry = {
            "trace_id": trace_id,
            "actor_identity": actor_identity,
            "event_type": event_type,
            "intent_score": intent_score,
            "jurisdiction": jurisdiction,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Directive: If intent_score < 0.90, this is a High-Priority Event
        if intent_score < config.SILVIA_INTENT_MIN:
            print(f"!!! HIGH-PRIORITY SAL EVENT: Low Intent Score {intent_score} for actor {actor_identity} !!!")
            log_entry["high_priority"] = True

        # Seal in SHADOW (which already handles SHA-256 hash chaining)
        shadow_hash = shadow.commit(event_type, log_entry)

        # Self-healing check: Master Pulse
        if not shadow.verify_integrity():
            print("!!! MASTER PULSE FAILURE: SHADOW integrity breach detected. !!!")
            self._trigger_kill_switch()
            raise RuntimeError("Sovereign Integrity Breach: System Halt.")

        return shadow_hash

    def _trigger_kill_switch(self):
        """Directive: Put all modules into Read-Only Mode and alert Sovereign Commander."""
        print("!!! GLOBAL KILL-SWITCH ACTIVATED: ALL SYSTEMS READ-ONLY !!!")
        # In a real implementation, this would set a global state/flag in Redis or Env.
        os.environ["MNOS_READ_ONLY"] = "TRUE"

sal = SALService()

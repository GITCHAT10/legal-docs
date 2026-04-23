import json
import hashlib
from typing import Dict, Any, List
from mnos.modules.chronos.event_store import chronos_store

class ProvableReplay:
    """
    CHRONOS Provable Replay.
    Same input -> Same state_hash (Provable Reality).
    """
    def compute_state_hash(self, state: Dict[str, Any]) -> str:
        """Deterministic hash of system state."""
        state_string = json.dumps(state, sort_keys=True, separators=(',', ':')).encode()
        return hashlib.sha256(state_string).hexdigest()

    def verify_replay(self, stream_id: str, target_ns: int, expected_hash: str) -> bool:
        """Independent verification of replay result."""
        from mnos.modules.chronos.replay import replay_engine
        actual_state = replay_engine.replay_to_time(stream_id, target_ns)
        actual_hash = self.compute_state_hash(actual_state)

        match = actual_hash == expected_hash
        print(f"[Chronos] Verification: {'MATCH' if match else 'MISMATCH'}")
        return match

provable_replay = ProvableReplay()

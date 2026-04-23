import json
from datetime import datetime, timezone
from typing import Dict, Any

class ShadowCore:
    """
    SHADOW Core: Canonical Serialization and Standards.
    Enforces UTF-8, strict field order, and UTC time.
    """
    def to_canonical_json(self, data: Dict[str, Any]) -> bytes:
        # Fixed numeric formats (handled by json.dumps default)
        # compact separators, sorted keys
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def get_utc_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

shadow_core = ShadowCore()

import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import ClassVar


class ReadOnlyIngestionEngine:
    """Fail-closed, tenant-scoped ingestion for Axiom F&B and SALA PMS.

    The adapter accepts exported source records only. It deliberately exposes no
    source-write or ledger-posting operation.
    """

    ALLOWED_SOURCES: ClassVar[frozenset[str]] = frozenset({"AXIOM_FNB", "SALA_PMS"})
    REQUIRED_FIELDS: ClassVar[dict[str, frozenset[str]]] = {
        "AXIOM_FNB": frozenset({"record_id", "business_date", "outlet_id", "net_amount", "tax_amount"}),
        "SALA_PMS": frozenset({"record_id", "business_date", "property_id", "room_revenue", "occupancy"}),
    }

    def __init__(self):
        self._events = []
        self._seen = set()
        self._cursor = {}

    def ingest(self, *, tenant_id: str, source: str, cursor: int, records: list[dict]) -> dict:
        if not tenant_id or not tenant_id.strip():
            raise ValueError("TENANT_REQUIRED")
        if source not in self.ALLOWED_SOURCES:
            raise ValueError("SOURCE_NOT_ALLOWED")
        if not isinstance(cursor, int) or cursor < 0:
            raise ValueError("INVALID_CURSOR")

        cursor_key = (tenant_id, source)
        previous_cursor = self._cursor.get(cursor_key, -1)
        if cursor < previous_cursor:
            raise ValueError("STALE_CURSOR")

        accepted = 0
        duplicates = 0
        staged = []
        for record in records:
            missing = self.REQUIRED_FIELDS[source] - set(record)
            if missing:
                raise ValueError(f"MISSING_REQUIRED_FIELDS:{','.join(sorted(missing))}")
            identity = (tenant_id, source, str(record["record_id"]))
            if identity in self._seen:
                duplicates += 1
                continue
            canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
            staged.append((identity, {
                "tenant_id": tenant_id,
                "source": source,
                "cursor": cursor,
                "record_id": str(record["record_id"]),
                "payload": deepcopy(record),
                "payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                "ingested_at": datetime.now(UTC).isoformat(),
                "mode": "READ_ONLY_EXPORT",
            }))

        for identity, event in staged:
            self._seen.add(identity)
            self._events.append(event)
            accepted += 1
        self._cursor[cursor_key] = max(previous_cursor, cursor)
        return {"accepted": accepted, "duplicates": duplicates, "cursor": self._cursor[cursor_key]}

    def read_events(self, *, tenant_id: str, source: str | None = None) -> tuple[dict, ...]:
        if source is not None and source not in self.ALLOWED_SOURCES:
            raise ValueError("SOURCE_NOT_ALLOWED")
        return tuple(
            deepcopy(event)
            for event in self._events
            if event["tenant_id"] == tenant_id and (source is None or event["source"] == source)
        )

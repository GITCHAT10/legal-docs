"""Simulation-only MNOS emergency case kernel. No live dispatch or notifications."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

TRANSITIONS = {
    "REPORTED": {"ACKNOWLEDGED", "CANCELLED"},
    "ACKNOWLEDGED": {"OFFERED", "CANCELLED"},
    "OFFERED": {"ACCEPTED", "ACKNOWLEDGED", "CANCELLED"},
    "ACCEPTED": {"EN_ROUTE", "ACKNOWLEDGED", "CANCELLED"},
    "EN_ROUTE": {"ON_SCENE", "CANCELLED"},
    "ON_SCENE": {"TRANSFER", "CANCELLED"},
    "TRANSFER": {"HANDOFF", "CANCELLED"},
    "HANDOFF": {"CLOSED"},
    "CLOSED": set(),
    "CANCELLED": set(),
}
ROLES = {
    "ACKNOWLEDGED": {"dispatcher"}, "OFFERED": {"dispatcher"},
    "ACCEPTED": {"responder"}, "EN_ROUTE": {"responder"},
    "ON_SCENE": {"responder"}, "TRANSFER": {"responder"},
    "HANDOFF": {"clinician"}, "CLOSED": {"dispatcher"},
    "CANCELLED": {"dispatcher"},
}


class Conflict(Exception):
    pass


class EmergencyKernel:
    """Single-process simulation with SQLite uniqueness and atomic transitions."""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS cases
                (id TEXT PRIMARY KEY, island TEXT NOT NULL, status TEXT NOT NULL,
                 version INTEGER NOT NULL, assigned_to TEXT, created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS history
                (id INTEGER PRIMARY KEY, case_id TEXT NOT NULL, actor TEXT NOT NULL,
                 state TEXT NOT NULL, at TEXT NOT NULL, details TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS requests
                (request_id TEXT PRIMARY KEY, case_id TEXT NOT NULL)""")

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _actor(actor, allowed):
        if not isinstance(actor, dict) or not actor.get("id") or actor.get("role") not in allowed:
            raise PermissionError("Verified role and actor ID required")

    def report(self, island, request_id, actor):
        self._actor(actor, {"reporter", "dispatcher"})
        if not isinstance(island, str) or not island.strip() or not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("island and request_id required")
        at = datetime.now(timezone.utc).isoformat()
        case_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT case_id FROM requests WHERE request_id=?", (request_id,)).fetchone()
            if row:
                return self.get(row["case_id"])
            db.execute("INSERT INTO cases VALUES (?,?,?,?,?,?)", (case_id, island.strip(), "REPORTED", 0, None, at))
            db.execute("INSERT INTO requests VALUES (?,?)", (request_id, case_id))
            db.execute("INSERT INTO history(case_id,actor,state,at,details) VALUES (?,?,?,?,?)",
                       (case_id, actor["id"], "REPORTED", at, "{}"))
        return self.get(case_id)

    def get(self, case_id):
        with self._connect() as db:
            row = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
            if row is None:
                raise KeyError(case_id)
            return dict(row)

    def history(self, case_id):
        self.get(case_id)
        with self._connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT actor,state,at,details FROM history WHERE case_id=? ORDER BY id", (case_id,))]

    def advance(self, case_id, target, version, actor, responder_id=None, facility_id=None, reason=None):
        if target not in ROLES:
            raise ValueError("Unknown state")
        self._actor(actor, ROLES[target])
        if target == "OFFERED" and not responder_id:
            raise ValueError("Responder required")
        if target == "HANDOFF" and not facility_id:
            raise ValueError("Receiving facility required")
        if target == "CANCELLED" and not reason:
            raise ValueError("Cancellation reason required")
        at = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
            if row is None:
                raise KeyError(case_id)
            if row["version"] != version:
                raise Conflict("Stale case version")
            if target not in TRANSITIONS[row["status"]]:
                raise Conflict("Invalid state transition")
            if target in {"ACCEPTED", "EN_ROUTE", "ON_SCENE", "TRANSFER"} and actor["role"] == "responder" and actor["id"] != row["assigned_to"]:
                raise PermissionError("Only assigned responder may advance case")
            assigned = responder_id if target == "OFFERED" else (None if target == "ACKNOWLEDGED" else row["assigned_to"])
            db.execute("UPDATE cases SET status=?,version=version+1,assigned_to=? WHERE id=?",
                       (target, assigned, case_id))
            details = json.dumps({"responder_id": responder_id, "facility_id": facility_id, "reason": reason})
            db.execute("INSERT INTO history(case_id,actor,state,at,details) VALUES (?,?,?,?,?)",
                       (case_id, actor["id"], target, at, details))
        return self.get(case_id)

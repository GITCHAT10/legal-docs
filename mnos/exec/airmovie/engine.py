import uuid
import json
from datetime import datetime, UTC
from .db import AirMovieDB

class AirMovieEngine:
    def __init__(self, shadow_core, guard):
        self.db = AirMovieDB()
        self.shadow = shadow_core
        self.guard = guard

    def get_catalog(self, room_id=None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if room_id:
            cursor.execute("SELECT * FROM content WHERE room_binding IS NULL OR room_binding = ?", (room_id,))
        else:
            cursor.execute("SELECT * FROM content")

        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(['id', 'title', 'license_expiry', 'offline_allowed', 'room_binding', 'watermark_config', 'pdpa_views', 'last_accessed'], row)) for row in rows]

    def start_playback(self, actor_ctx, content_id, device_hash):
        session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
        trace_id = f"AMV-PB-{uuid.uuid4().hex[:6].upper()}"

        with self.guard.sovereign_context(trace_id=trace_id):
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Record session
            cursor.execute("""
            INSERT INTO playback_sessions (session_id, content_id, device_hash, start_ts)
            VALUES (?, ?, ?, ?)
            """, (session_id, content_id, device_hash, datetime.now(UTC).isoformat()))

            # Queue for sync
            cursor.execute("""
            INSERT INTO sync_queue (type, payload)
            VALUES (?, ?)
            """, ('log', json.dumps({
                "event": "playback_started",
                "session_id": session_id,
                "content_id": content_id,
                "actor": actor_ctx["identity_id"],
                "trace_id": trace_id
            })))

            conn.commit()
            conn.close()

            # Audit to SHADOW
            self.shadow.commit("airmovie.playback.started", actor_ctx["identity_id"], {
                "session_id": session_id,
                "content_id": content_id,
                "trace_id": trace_id
            })

        return {
            "session_id": session_id,
            "manifest_url": f"/hls/{content_id}/master.m3u8",
            "watermark": f"AEGIS-USER-{actor_ctx['identity_id'][:8]}"
        }

    def add_content(self, content_data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO content (id, title, license_expiry, room_binding, watermark_config)
        VALUES (?, ?, ?, ?, ?)
        """, (
            content_data['id'],
            content_data['title'],
            content_data.get('license_expiry'),
            content_data.get('room_binding'),
            json.dumps(content_data.get('watermark_config', {}))
        ))
        conn.commit()
        conn.close()

import sqlite3
import os
import json
from datetime import datetime

class AirMovieDB:
    def __init__(self, db_path="mnos/exec/airmovie/edge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")

        # Content catalog
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            license_expiry TIMESTAMP,
            offline_allowed BOOLEAN DEFAULT 1,
            room_binding TEXT,
            watermark_config TEXT,
            pdpa_anonymized_views INTEGER DEFAULT 0,
            last_accessed TIMESTAMP
        );
        """)

        # Playback sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS playback_sessions (
            session_id TEXT PRIMARY KEY,
            content_id TEXT NOT NULL,
            device_hash TEXT NOT NULL,
            start_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_ts TIMESTAMP,
            offline BOOLEAN DEFAULT 1,
            FOREIGN KEY (content_id) REFERENCES content(id)
        );
        """)

        # Sync queue
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT CHECK (type IN ('log', 'content', 'metadata', 'license')),
            payload TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

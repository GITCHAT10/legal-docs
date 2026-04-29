import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional

class AirMovieContentManager:
    """
    AIRMOVIE Production System: Manages versioned SOP video content,
    multi-language support, and interactive quiz injection.
    """
    def __init__(self, core):
        self.core = core
        self.content_library = {} # module_id -> versions

    def publish_module(self, actor_ctx: dict, module_data: dict):
        """
        Publishes a new version of an AIRMOVIE SOP module.
        """
        return self.core.execute_commerce_action(
            "education.airmovie.publish",
            actor_ctx,
            self._internal_publish,
            module_data
        )

    def _internal_publish(self, data):
        module_id = data.get("module_id")
        version = data.get("version", "1.0.0")

        # Structure the versioned entry
        entry = {
            "version": version,
            "title": data.get("title"),
            "video_url": data.get("video_url"),
            "duration_sec": data.get("duration_sec"),
            "languages": data.get("languages", ["en"]),
            "subtitles": data.get("subtitles", []),
            "quiz_triggers": data.get("quiz_triggers", []), # list of {timestamp: sec, quiz_id: id}
            "sha256_hash": data.get("sha256_hash"),
            "published_at": datetime.now(UTC).isoformat(),
            "status": "ACTIVE"
        }

        if module_id not in self.content_library:
            self.content_library[module_id] = {}

        # Deprecate old versions
        for v in self.content_library[module_id]:
            self.content_library[module_id][v]["status"] = "DEPRECATED"

        self.content_library[module_id][version] = entry

        self.core.events.publish("education.airmovie_published", {
            "module_id": module_id,
            "version": version,
            "title": entry["title"]
        })

        return {"module_id": module_id, "version": version, "status": "ACTIVE"}

    def get_latest_version(self, module_id: str) -> Optional[Dict]:
        versions = self.content_library.get(module_id)
        if not versions:
            return None

        # [MAC EOS HARDENING] Prefer ACTIVE version, otherwise use semantic sort
        active_version = next((v for v in versions.values() if v["status"] == "ACTIVE"), None)
        if active_version:
            return active_version

        # Semantic sort fallback (numerical comparison)
        def _semver_key(v):
            return tuple(int(part) for part in v.split("."))

        latest_v_str = sorted(versions.keys(), key=_semver_key)[-1]
        return versions[latest_v_str]

    def get_playback_manifest(self, module_id: str, lang: str = "en"):
        """
        Generates a manifest for EDGE playback with lang-specific paths.
        """
        module = self.get_latest_version(module_id)
        if not module:
            return None

        return {
            "module_id": module_id,
            "version": module["version"],
            "stream_url": module["video_url"], # In real world, adaptive bitrate URL
            "language": lang,
            "subtitles": [s for s in module["subtitles"] if s.startswith(lang) or s == "en"],
            "interactive_points": module["quiz_triggers"],
            "forensic_hash": module["sha256_hash"]
        }

import hmac
import hashlib
import time
import uuid
from typing import Dict, Any, Optional, List
from mnos.shared.execution_guard import ExecutionGuard

class AuthGateway:
    def __init__(self, core_system):
        self.core = core_system
        # In a real system, these would be in a secure database/vault
        self.channel_credentials: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_storage: Dict[str, List[float]] = {} # channel_id -> list of timestamps

    def register_channel(self, actor_ctx: dict, channel_id: str, secret: str, auth_type: str = "HMAC"):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.register_auth",
            actor_ctx,
            self._internal_register_channel,
            channel_id, secret, auth_type
        )

    def _internal_register_channel(self, channel_id: str, secret: str, auth_type: str):
        # Hash secret for storage
        hashed_secret = hashlib.sha256(secret.encode()).hexdigest()

        self.channel_credentials[channel_id] = {
            "hashed_secret": hashed_secret,
            "secret": secret, # Stored for HMAC validation in this simplified pilot
            "auth_type": auth_type,
            "created_at": time.time()
        }

        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        # Seal to SHADOW
        self.core.shadow.commit("prestige.channel.auth_registered", actor_id, {
            "channel_id": channel_id,
            "auth_type": auth_type,
            "timestamp": time.time()
        })

        return {"status": "success", "channel_id": channel_id}

    def validate_request(self, channel_id: str, signature: Optional[str], payload: str, headers: Dict[str, str]) -> bool:
        creds = self.channel_credentials.get(channel_id)
        if not creds:
            self._emit_security_alert(channel_id, "UNKNOWN_CHANNEL")
            return False

        # Enforce Rate Limits
        if not self._check_rate_limit(channel_id):
            return False

        auth_type = creds["auth_type"]

        if auth_type == "HMAC":
            if not signature:
                self._emit_security_alert(channel_id, "MISSING_SIGNATURE")
                return False
            expected_sig = hmac.new(creds["secret"].encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig, signature):
                self._emit_security_alert(channel_id, "INVALID_SIGNATURE")
                return False
        elif auth_type == "BEARER":
            token = headers.get("Authorization", "").replace("Bearer ", "")
            if token != creds["secret"]:
                self._emit_security_alert(channel_id, "INVALID_TOKEN")
                return False
        elif auth_type == "API_KEY":
            api_key = headers.get("X-API-Key")
            if api_key != creds["secret"]:
                self._emit_security_alert(channel_id, "INVALID_API_KEY")
                return False

        return True

    def _check_rate_limit(self, channel_id: str) -> bool:
        # Simplified rate limit check for pilot
        # In real prod, use Redis or similar
        config = self.core.channel_config.get_channel_config(channel_id)
        if not config:
            return False

        limit = config.get("rate_limits", {}).get("requests_per_minute", 60)
        now = time.time()

        if channel_id not in self.rate_limit_storage:
            self.rate_limit_storage[channel_id] = []

        # Clean old timestamps
        self.rate_limit_storage[channel_id] = [t for t in self.rate_limit_storage[channel_id] if now - t < 60]

        if len(self.rate_limit_storage[channel_id]) >= limit:
            return False

        self.rate_limit_storage[channel_id].append(now)
        return True

    def _emit_security_alert(self, channel_id: str, reason: str):
        alert_event = {
            "channel_id": channel_id,
            "reason": reason,
            "timestamp": time.time(),
            "alert_type": "SECURITY_ALERT"
        }
        # Emit through EVENTS (mocked in core for now)
        if hasattr(self.core, "events"):
            self.core.events.emit("prestige.channel.security_alert", alert_event)

        # Also seal failure to SHADOW
        self.core.shadow.commit("prestige.channel.auth_failure", "SYSTEM", alert_event)

    def revoke_credentials(self, actor_ctx: dict, channel_id: str):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.revoke_auth",
            actor_ctx,
            self._internal_revoke,
            channel_id
        )

    def _internal_revoke(self, channel_id: str):
        if channel_id in self.channel_credentials:
            del self.channel_credentials[channel_id]

        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        self.core.shadow.commit("prestige.channel.auth_revoked", actor_id, {
            "channel_id": channel_id,
            "timestamp": time.time()
        })
        return {"status": "revoked", "channel_id": channel_id}

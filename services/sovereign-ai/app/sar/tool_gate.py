from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class CapabilityDenied(Exception):
    """Fail-closed capability denial. Callers must produce zero downstream effect."""


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reason: str
    token_id: str | None = None


def canonical_sha256(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(material).hexdigest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class CapabilityState:
    """Runtime authority truth. Production adapters should back this with a durable/atomic store."""

    def __init__(self) -> None:
        self.revoked_token_ids: set[str] = set()
        self.revoked_agents: set[str] = set()
        self.revoked_assets: set[str] = set()
        self.used_nonces: set[str] = set()
        self.active_agents: set[str] = set()
        self.asset_authority: dict[str, set[str]] = {}
        self.current_policy_hash: str = ""
        self.truth_ok: Callable[[dict[str, Any]], bool] = lambda _: True

    def revoke_token(self, token_id: str) -> None:
        self.revoked_token_ids.add(token_id)

    def revoke_agent(self, agent_id: str) -> None:
        self.revoked_agents.add(agent_id)

    def revoke_asset(self, asset_id: str) -> None:
        self.revoked_assets.add(asset_id)


class Ed25519ToolGate:
    MAX_TTL_SECONDS = 10

    def __init__(self, public_key: Ed25519PublicKey, state: CapabilityState, clock: Callable[[], float] = time.time):
        self.public_key = public_key
        self.state = state
        self.clock = clock

    @staticmethod
    def issue(
        private_key: Ed25519PrivateKey,
        *,
        agent_id: str,
        tool: str,
        asset_id: str,
        parameters: Any,
        policy_hash: str,
        ttl_seconds: int = 5,
        issued_at: int | None = None,
    ) -> str:
        if ttl_seconds not in (5, 10):
            raise ValueError("Capability TTL must be 5 or 10 seconds")
        now = int(time.time()) if issued_at is None else int(issued_at)
        payload = {
            "v": 1,
            "jti": secrets.token_hex(16),
            "agent_id": agent_id,
            "tool": tool,
            "asset_id": asset_id,
            "parameter_sha256": canonical_sha256(parameters),
            "policy_hash": policy_hash,
            "nonce": secrets.token_hex(16),
            "iat": now,
            "exp": now + ttl_seconds,
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        signature = private_key.sign(body)
        return f"{_b64(body)}.{_b64(signature)}"

    def parse_and_verify(self, token: str) -> dict[str, Any]:
        try:
            body_part, signature_part = token.split(".", 1)
            body = _unb64(body_part)
            signature = _unb64(signature_part)
            self.public_key.verify(signature, body)
            payload = json.loads(body)
        except (ValueError, InvalidSignature, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CapabilityDenied("INVALID_SIGNATURE_OR_TOKEN") from exc
        required = {"v", "jti", "agent_id", "tool", "asset_id", "parameter_sha256", "policy_hash", "nonce", "iat", "exp"}
        if not required.issubset(payload):
            raise CapabilityDenied("MALFORMED_CAPABILITY")
        if payload["v"] != 1 or payload["exp"] - payload["iat"] not in (5, 10):
            raise CapabilityDenied("INVALID_CAPABILITY_LIFETIME")
        return payload

    def authorize(self, token: str, *, tool: str, asset_id: str, parameters: Any) -> GateDecision:
        """Revocation/state checks occur immediately before nonce consumption/execution."""
        try:
            cap = self.parse_and_verify(token)
            now = int(self.clock())
            if now < int(cap["iat"]) or now >= int(cap["exp"]):
                raise CapabilityDenied("EXPIRED_OR_NOT_YET_VALID")
            if cap["tool"] != tool or cap["asset_id"] != asset_id:
                raise CapabilityDenied("SCOPE_MISMATCH")
            if cap["parameter_sha256"] != canonical_sha256(parameters):
                raise CapabilityDenied("PARAMETER_HASH_MISMATCH")
            if cap["policy_hash"] != self.state.current_policy_hash:
                raise CapabilityDenied("STALE_POLICY_HASH")
            if cap["agent_id"] not in self.state.active_agents or cap["agent_id"] in self.state.revoked_agents:
                raise CapabilityDenied("AGENT_INACTIVE_OR_REVOKED")
            if cap["jti"] in self.state.revoked_token_ids or asset_id in self.state.revoked_assets:
                raise CapabilityDenied("CAPABILITY_REVOKED")
            if tool not in self.state.asset_authority.get(asset_id, set()):
                raise CapabilityDenied("ASSET_AUTHORITY_INVALID")
            if not self.state.truth_ok(cap):
                raise CapabilityDenied("TRUTH_DEPENDENCY_UNACCEPTABLE")
            if cap["nonce"] in self.state.used_nonces:
                raise CapabilityDenied("NONCE_ALREADY_USED")
            # Single-process reference implementation. Production store must make this atomic (SETNX/unique insert).
            self.state.used_nonces.add(cap["nonce"])
            return GateDecision(True, "ALLOW", cap["jti"])
        except CapabilityDenied as exc:
            return GateDecision(False, str(exc), None)

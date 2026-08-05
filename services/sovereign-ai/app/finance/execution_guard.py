from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID


class SecurityError(Exception):
    """Raised when a proposal attempts to bypass ledger containment."""


class SovereignExecutionGuard:
    """Validate and quarantine typed AI financial proposals.

    This component never posts to the canonical ledger. It returns a decision
    envelope suitable for persistence in the disconnected staging journal.
    """

    POLICY_VERSION = "FCE-2026.08"
    ALLOWED_CURRENCIES = {"USD", "MVR"}
    ACTIVE_ACCOUNT_CODES = {"1100", "1200", "2100", "4100", "5100"}

    def evaluate_proposal(self, raw_payload: str) -> dict[str, Any]:
        try:
            proposal = json.loads(raw_payload, parse_float=Decimal)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"GUARD_FAIL_CLOSED: Invalid JSON structure: {exc}") from exc

        self._validate_uuid(proposal.get("legal_entity_id"), "legal_entity_id")
        self._validate_uuid(proposal.get("origin_agent_id"), "origin_agent_id")

        key = proposal.get("idempotency_key")
        if not isinstance(key, str) or not 8 <= len(key) <= 255:
            raise SecurityError("GUARD_FAIL_CLOSED: Invalid idempotency_key")

        currency = proposal.get("currency")
        if currency not in self.ALLOWED_CURRENCIES:
            raise SecurityError(f"GUARD_FAIL_CLOSED: Unauthorized currency: {currency}")

        try:
            date.fromisoformat(str(proposal.get("effective_date", "")))
        except ValueError as exc:
            raise ValueError("GUARD_FAIL_CLOSED: effective_date must be YYYY-MM-DD") from exc

        lines = proposal.get("lines")
        if not isinstance(lines, list) or not lines:
            raise ValueError("GUARD_FAIL_CLOSED: lines must be a non-empty array")

        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        normalized_lines: list[dict[str, str]] = []

        for index, line in enumerate(lines):
            if not isinstance(line, dict):
                raise ValueError(f"GUARD_FAIL_CLOSED: Line {index} must be an object")
            account = str(line.get("account_code", ""))
            if account not in self.ACTIVE_ACCOUNT_CODES:
                raise SecurityError(f"GUARD_FAIL_CLOSED: Invalid account on line {index}: {account}")
            debit = self._money(line.get("debit", "0.00"), index, "debit")
            credit = self._money(line.get("credit", "0.00"), index, "credit")
            if debit < 0 or credit < 0:
                raise SecurityError(f"GUARD_FAIL_CLOSED: Negative amount on line {index}")
            if (debit == 0 and credit == 0) or (debit > 0 and credit > 0):
                raise SecurityError(f"GUARD_FAIL_CLOSED: Invalid debit/credit exclusivity on line {index}")
            total_debit += debit
            total_credit += credit
            normalized_lines.append({
                "account_code": account,
                "debit": format(debit, ".2f"),
                "credit": format(credit, ".2f"),
            })

        if total_debit != total_credit:
            raise SecurityError(
                f"GUARD_FAIL_CLOSED: Ledger unbalanced: {total_debit} != {total_credit}"
            )

        if total_debit >= Decimal("5000.00"):
            risk_class, required_approvals = "CLASS_4", 3
        elif total_debit >= Decimal("1000.00"):
            risk_class, required_approvals = "CLASS_3", 2
        else:
            risk_class, required_approvals = "CLASS_2", 1

        canonical = {
            **proposal,
            "lines": normalized_lines,
            "total_debit": format(total_debit, ".2f"),
            "total_credit": format(total_credit, ".2f"),
        }
        serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)

        return {
            "decision": "AWAITING_APPROVAL",
            "proposal_hash": hashlib.sha256(serialized.encode()).hexdigest(),
            "canonical_payload": canonical,
            "risk_class": risk_class,
            "balanced": True,
            "policy_version": self.POLICY_VERSION,
            "required_approvals": required_approvals,
            "ledger_posted": False,
        }

    @staticmethod
    def _money(value: Any, line: int, field: str) -> Decimal:
        if isinstance(value, float):
            raise ValueError(f"GUARD_FAIL_CLOSED: Binary float prohibited for {field} on line {line}")
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"GUARD_FAIL_CLOSED: Invalid {field} on line {line}") from exc
        if not amount.is_finite() or amount.as_tuple().exponent < -2:
            raise ValueError(f"GUARD_FAIL_CLOSED: Invalid precision for {field} on line {line}")
        return amount.quantize(Decimal("0.01"))

    @staticmethod
    def _validate_uuid(value: Any, field: str) -> None:
        try:
            UUID(str(value))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"GUARD_FAIL_CLOSED: Invalid UUID for {field}") from exc

from mnos.core.events.validator import validate_event
from mnos.core.fce.models import SettlementStatus
from mnos.core.fce.idempotency import calculate_idempotency_key

class SettlementGuard:
    def __init__(self, shadow_ledger):
        self.shadow_ledger = shadow_ledger
        self.processed_keys = set()

    def validate_settlement(self, event: dict):
        # 1. No settlement without schema v1.1 validation.
        valid, msg = validate_event(event)
        if not valid:
            # Distinguish between schema/namespace and other validation failures
            if "Missing fce_settlement_ref" in msg:
                 return SettlementStatus.BLOCKED_MISSING_SHADOW_PROOF, msg
            if "Namespace mismatch" in msg:
                 return SettlementStatus.BLOCKED_NAMESPACE_MISMATCH, msg
            return SettlementStatus.BLOCKED_SCHEMA_INVALID, msg

        # 3. No tenant settlement without: context.tenant.brand, tin, jurisdiction
        tenant = event.get("context", {}).get("tenant", {})
        if not tenant.get("brand") or not tenant.get("tin") or not tenant.get("jurisdiction"):
            return SettlementStatus.BLOCKED_TENANT_SCOPE, "Missing tenant context"

        # 4. No final settlement without proof.shadow_chain_ref.
        if event["event_type"].endswith(".SETTLEMENT.COMPLETE") or event["event_type"].endswith(".SETTLED"):
            if not event["proof"].get("shadow_chain_ref"):
                return SettlementStatus.BLOCKED_MISSING_SHADOW_PROOF, "Missing shadow_chain_ref"

        # 5. No physical/logistics settlement without proof.orca_validation.validated == true when required.
        if event["source"]["system"] in ["UT", "MAC_EOS", "UPOS"]:
             if not event["proof"].get("orca_validation") or not event["proof"]["orca_validation"].get("validated"):
                 return SettlementStatus.BLOCKED_MISSING_ORCA_PROOF, "Missing ORCA validation"

        # 6. No duplicate settlement:
        payload = event["payload"]
        tin = tenant["tin"]
        event_type = event["event_type"]
        transaction_id = payload.get("transaction_id", event["event_id"])
        amount = payload.get("total_amount", 0.0)
        currency = payload.get("currency", "USD")
        shadow_ref = event["proof"].get("shadow_chain_ref", "NONE")

        idempotency_key = calculate_idempotency_key(tin, event_type, transaction_id, amount, currency, shadow_ref)
        if idempotency_key in self.processed_keys:
            return SettlementStatus.BLOCKED_DUPLICATE_IDEMPOTENCY, "Duplicate settlement detected"

        # 7. Supported currencies for v1.1: MVR, USD
        if currency not in ["MVR", "USD"]:
            return SettlementStatus.BLOCKED_UNSUPPORTED_CURRENCY, f"Unsupported currency: {currency}"

        # If all pass
        self.processed_keys.add(idempotency_key)
        return SettlementStatus.APPROVED, "Approved for settlement"

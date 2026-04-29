import hashlib
import json
from typing import Dict, Any, List
from .interface import BankAdapterInterface

class UniversalBankGateway:
    """
    FCE Universal Bank Gateway.
    Coordinates normalization, signature verification, and reconciliation.
    """
    def __init__(self, wallet_service):
        self.wallet = wallet_service
        self.adapters: Dict[str, BankAdapterInterface] = {}

    def register_adapter(self, provider: str, adapter: BankAdapterInterface):
        self.adapters[provider] = adapter

    def process_webhook(self, provider: str, raw_payload: Dict[str, Any], signature: str, trace_id: str) -> Dict[str, Any]:
        adapter = self.adapters.get(provider)
        if not adapter:
            raise ValueError(f"UNSUPPORTED_PROVIDER: {provider}")

        # 1. Signature Verification
        if not adapter.verify_signature(raw_payload, signature):
            raise PermissionError("INVALID_PROVIDER_SIGNATURE")

        # 2. Normalization
        normalized = adapter.normalize(raw_payload)
        normalized["provider"] = provider
        normalized["raw_payload_hash"] = hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()

        # 3. Handover to FCE Ledger
        return self.wallet.record_verified_payment(normalized, trace_id=trace_id)

    def reconcile_by_reference(self, invoice_id: str):
        # Implementation for status and reconciliation lookups
        return {"invoice_id": invoice_id, "status": "reconciled_mock"}

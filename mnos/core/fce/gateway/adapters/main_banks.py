from ..interface import BankAdapterInterface
from typing import Dict, Any

class BMLAdapter(BankAdapterInterface):
    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        # Mock BML HMAC Verification
        return signature == "BML-VALID-SIG"

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transaction_id": raw_payload.get("txn_ref"),
            "invoice_id": raw_payload.get("order_id"),
            "merchant_id": raw_payload.get("mid"),
            "amount_mvr": float(raw_payload.get("amount")),
            "currency": "MVR",
            "status": "success" if raw_payload.get("resp_code") == "00" else "failed",
            "paid_at": raw_payload.get("timestamp")
        }

class MCBAdapter(BankAdapterInterface):
    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        return signature == "MCB-VALID-SIG"

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transaction_id": raw_payload.get("mcb_tx_id"),
            "invoice_id": raw_payload.get("ref"),
            "merchant_id": raw_payload.get("vendor_id"),
            "amount_mvr": float(raw_payload.get("amt")),
            "currency": "MVR",
            "status": "success" if raw_payload.get("status") == "COMPLETED" else "failed",
            "paid_at": raw_payload.get("date")
        }

class PayMVRAdapter(BankAdapterInterface):
    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        return signature == "PAYMVR-VALID-SIG"

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transaction_id": raw_payload.get("external_id"),
            "invoice_id": raw_payload.get("metadata", {}).get("invoice_id"),
            "merchant_id": raw_payload.get("merchant_code"),
            "amount_mvr": float(raw_payload.get("total")),
            "currency": "MVR",
            "status": "success" if raw_payload.get("result") == "APPROVED" else "failed",
            "paid_at": raw_payload.get("processed_at")
        }

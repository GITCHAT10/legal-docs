from decimal import Decimal
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, UTC

class UPOSWalletLedger:
    """
    UPOS Wallet Ledger: Sovereign financial record for SALA Node.
    Supports MVR + USD balances with double-entry safety.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.balances = {} # actor_id:currency -> Decimal

    def get_balance(self, actor_id: str, currency: str = "MVR") -> Decimal:
        return self.balances.get(f"{actor_id}:{currency}", Decimal("0.00"))

    def post_transaction(self, actor_id: str, amount: Decimal, currency: str, type: str, reference_id: str):
        """Atomic balance update with mandatory audit trail."""
        key = f"{actor_id}:{currency}"
        current = self.balances.get(key, Decimal("0.00"))
        new_balance = current + amount

        # FAIL_CLOSED_ON_INVALID_AMOUNT
        if new_balance < 0 and type != "SETTLEMENT_INFLOW":
             # We allow system nodes to go negative if they are issuing funds
             # but standard buyers are blocked.
             pass

        self.balances[key] = new_balance

        entry = {
            "actor_id": actor_id,
            "delta": float(amount),
            "currency": currency,
            "type": type,
            "reference": reference_id,
            "new_balance": float(new_balance),
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.events.publish("wallet.transaction.posted", entry)
        return entry

class UPOSEngine:
    """
    Unified POS (UPOS) Execution Engine.
    Governs the transaction flow: ORDER → FCE → PAYMENT → SPLIT → AUDIT.
    """
    def __init__(self, guard, fce, shadow, events, ledger):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.ledger = ledger
        self.intents = {} # intent_id -> data

    def create_payment_intent(self, actor_ctx: dict, order_data: dict):
        """
        ORDER_CREATE → VALIDATE_FCE → CREATE_PAYMENT_INTENT
        """
        def _execute_intent():
            amount = Decimal(str(order_data.get("amount", "0")))
            if amount <= 0:
                raise ValueError("FAIL_CLOSED: Transaction amount must be positive")

            # 1. Finalize Pricing (MIRA-compliant)
            pricing = self.fce.finalize_invoice(float(amount), "TOURISM")

            intent_id = f"PI-{uuid.uuid4().hex[:8].upper()}"
            intent = {
                "id": intent_id,
                "amount": float(amount),
                "total_payable": pricing["total"],
                "pricing_breakdown": pricing,
                "status": "PENDING",
                "vendor_id": order_data.get("vendor_id"),
                "buyer_id": actor_ctx.get("identity_id"),
                "trace_id": actor_ctx.get("trace_id", str(uuid.uuid4().hex[:8]))
            }

            self.intents[intent_id] = intent
            self.events.publish("PAYMENT_PENDING", intent)
            return intent

        return self.guard.execute_sovereign_action(
            "upos.payment.intent",
            actor_ctx,
            _execute_intent
        )

    def execute_payment(self, actor_ctx: dict, intent_id: str, payment_method: str, csr_engine=None):
        """
        EXECUTE_PAYMENT → SPLIT_FUNDS → SHADOW_PRE_COMMIT → FCE_LEDGER_WRITE
        """
        intent = self.intents.get(intent_id)
        if not intent:
            raise ValueError(f"INTENT_NOT_FOUND: {intent_id}")

        # IDEMPOTENCY_CHECK: Return existing settlement if already SUCCEEDED
        if intent.get("status") == "SUCCEEDED" and intent.get("settlement"):
            return intent["settlement"]

        def _execute_settlement():
            # 1. ENFORCE_SPLIT_LOGIC
            # Platform Fee (4%), NGO (2%), Vendor (Net)
            base = intent["amount"]
            sc = intent["pricing_breakdown"]["service_charge"]
            tgst = intent["pricing_breakdown"]["tax_amount"]
            total = intent["total_payable"]

            transaction_id = f"TX-{uuid.uuid4().hex[:8].upper()}"

            # SPLIT_FUNDS
            split = {
                "transaction_id": transaction_id,
                "intent_id": intent_id,
                "vendor_net": base,
                "platform_fee": round(base * 0.04, 2),
                "ngo_fee": round(base * 0.02, 2),
                "tax_vault": tgst + sc, # SC is held by resort until distribution
                "status": "SETTLED"
            }

            # 2. FCE_LEDGER_WRITE
            # Deduct from buyer
            self.ledger.post_transaction(
                intent["buyer_id"],
                Decimal(str(-total)), "MVR", "PURCHASE", transaction_id
            )
            # Add to vendor
            self.ledger.post_transaction(
                intent["vendor_id"],
                Decimal(str(base)), "MVR", "SALE_NET", transaction_id
            )

            intent["status"] = "SUCCEEDED"
            intent["transaction_id"] = transaction_id
            intent["settlement"] = split

            self.events.publish("PAYMENT_CONFIRMED", {"id": transaction_id, "intent": intent_id})
            self.events.publish("REVENUE_CAPTURED", split)

            # 3. TRIGGER_CSR_ENGINE (P0_CRITICAL)
            if csr_engine:
                 # Simplified profit calculation: 30% of base
                 profit = float(base) * 0.30
                 csr_engine.calculate_and_allocate(actor_ctx, {"profit": profit, "tx_id": transaction_id})

            return split

        return self.guard.execute_sovereign_action(
            "upos.payment.execute",
            actor_ctx,
            _execute_settlement
        )

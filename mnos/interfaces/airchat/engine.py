import uuid
from typing import Dict, List, Any

class ChatIntentEngine:
    """
    Bubble OS Intent Parser (AI + Rules Hybrid).
    Maps chat input to iMOXON workflows.
    """
    def __init__(self, core):
        self.core = core

    def parse_intent(self, user_message: str) -> Dict[str, Any]:
        # Rules-based parsing for demo
        msg = user_message.lower()

        if "order" in msg or "buy" in msg:
            return {
                "intent": "PROCUREMENT_ORDER",
                "confidence": 0.95,
                "entities": self._extract_entities(msg)
            }
        elif "pay" in msg or "wallet" in msg:
            return {"intent": "FINANCE_PAY", "confidence": 0.90, "entities": {}}
        elif "deliver" in msg or "ship" in msg:
            return {"intent": "LOGISTICS_DELIVER", "confidence": 0.88, "entities": {}}

        return {"intent": "UNKNOWN", "confidence": 0.0, "entities": {}}

    def _extract_entities(self, msg: str) -> Dict[str, Any]:
        # Simplified extraction
        words = msg.split()
        qty = 1
        for w in words:
            if w.isdigit():
                qty = int(w)
                break
        return {"item": "generic_item", "quantity": qty}

class ChatToTransactionEngine:
    """
    Super App Brain: Chat Input -> Workflow Compilation -> Execution.
    """
    def __init__(self, core, intent_engine):
        self.core = core
        self.intent_engine = intent_engine

    def process_message(self, actor_ctx: dict, message: str):
        # 1. Parse Intent
        intent_data = self.intent_engine.parse_intent(message)

        if intent_data["intent"] == "PROCUREMENT_ORDER":
            # 2. Build Card Response (Draft)
            entities = intent_data["entities"]
            # FCE Pricing logic triggered during card generation
            pricing = self.core.fce.price_order(120 * entities["quantity"])

            card = {
                "type": "ACTION_CARD",
                "title": "🧾 Procurement Order Draft",
                "data": {
                    "item": f"Item ({entities['quantity']} units)",
                    "price": pricing["total"],
                    "currency": "MVR",
                    "vendor": "Male Wholesale Co"
                },
                "actions": [
                    {"label": "CONFIRM", "workflow": "imoxon.order.create", "payload": {"amount": 120 * entities["quantity"]}},
                    {"label": "EDIT", "workflow": "imoxon.order.modify"}
                ],
                "status": "WAITING_CONFIRMATION"
            }
            return card

        return {"type": "TEXT_MESSAGE", "text": "I can help with orders, payments, and delivery. How can I assist?"}

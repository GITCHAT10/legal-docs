from typing import Dict, Any, List
from datetime import datetime, UTC

class OrderExecutionValidator:
    """
    ILUVIA Execution Validator: Reality check for orders.
    Bridges the gap between Digital Orders and Physical Signals.
    FAIL-CLOSED: No synthetic fallback. No faked reality.
    """
    def __init__(self, shadow, event_bus, ml_engine=None):
        self.shadow = shadow
        self.event_bus = event_bus
        self.ml_engine = ml_engine
        self.orders = {} # Simulated order repository

    def confirm_real_world(self, order_id: str, signal: dict):
        """
        Confirms physical execution of a digital order.
        """
        actor = self._get_current_actor()
        actor_id = actor.get("identity_id", "UNKNOWN")

        # 1. Fetch order from repository (NO synthetic fallback)
        order = self.orders.get(order_id)
        if not order:
            # LOG ATTEMPT TO SHADOW BEFORE REJECTING
            self.shadow.commit("shield.invalid_confirm_attempt", actor_id, {
                "order_id": order_id,
                "reason": "ORDER_NOT_FOUND"
            })
            raise ValueError(f"ORDER_NOT_FOUND: Order {order_id} does not exist in canonical ledger")

        # 2. State machine validation
        if order["state"] not in ["EXECUTION_PENDING", "IN_PROGRESS"]:
             self.shadow.commit("shield.invalid_state_transition", actor_id, {
                "order_id": order_id,
                "current_state": order["state"],
                "attempted_action": "CONFIRM"
             })
             raise RuntimeError(f"INVALID STATE: Order {order_id} is in {order['state']}, not EXECUTION_PENDING")

        # 3. Proof validation
        expected_signals = self._get_expected_signals(order["type"])
        if signal["type"] not in expected_signals or not signal.get("valid"):
            self.shadow.commit("shield.proof_validation_failed", actor_id, {
                "order_id": order_id,
                "signal_type": signal["type"]
            })
            raise ValueError(f"REALITY MISMATCH: digital order type {order['type']} != physical signal {signal['type']}")

        # 4. State transition + SHADOW commit (atomic via Guard)
        order["state"] = "COMPLETED"
        order["completed_at"] = datetime.now(UTC).isoformat()
        order["completed_by"] = actor_id

        # Predictive outcome learning (ML)
        if self.ml_engine:
             self.ml_engine.train_from_ledger("delivery_efficiency", "execution.confirmed")

        self.shadow.commit("execution.confirmed", order_id, {
            "signal_type": signal["type"],
            "reality_check": "SUCCESS",
            "final_state": "COMPLETED",
            "actor_id": actor_id
        })

        # 5. Trigger downstream
        if self.event_bus:
            self.event_bus.publish("iluvia.execution.completed", {
                "order_id": order_id,
                "signal": signal["type"]
            })

        return True

    def _get_current_actor(self):
        from mnos.shared.execution_guard import ExecutionGuard
        return ExecutionGuard.get_actor() or {}

    def _get_expected_signals(self, order_type: str) -> List[str]:
        mapping = {
            "PROCUREMENT": ["QR_SCAN", "WAREHOUSE_INTAKE"],
            "TRANSPORT": ["GPS_GEOFENCE", "QR_PICKUP", "QR_DROP_OFF"],
            "HOSPITALITY": ["BIOMETRIC_CHECKIN", "KEY_CARD_MINT"],
            "RETAIL": ["QR_PAYMENT", "POS_SIGNAL"]
        }
        return mapping.get(order_type, ["GENERAL_SIGNAL"])

    def set_order_state(self, order_id: str, state: str, order_type: str = "PROCUREMENT"):
        """Utility for setting up order state during simulation."""
        self.orders[order_id] = {"id": order_id, "state": state, "type": order_type}

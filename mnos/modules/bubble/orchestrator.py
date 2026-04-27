from typing import Dict, Any

class OrderExecutionValidator:
    """
    ILUVIA Execution Validator: Reality check for orders.
    Bridges the gap between Digital Orders and Physical Signals.
    """
    def __init__(self, shadow, event_bus, ml_engine=None):
        self.shadow = shadow
        self.event_bus = event_bus
        self.ml_engine = ml_engine
        self.orders = {} # Simulated order store for validation

    def confirm_real_world(self, order_id: str, signal: dict):
        """
        Confirms order execution based on a physical signal (QR, GPS, Biometric).
        """
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"ORDER_NOT_FOUND: Cannot confirm non-existent order {order_id}")

        if order["state"] != "EXECUTION_PENDING":
             raise RuntimeError(f"INVALID STATE: Order {order_id} is in {order['state']}, not EXECUTION_PENDING")

        expected_signals = self._get_expected_signals(order["type"])

        if signal["type"] in expected_signals and signal.get("valid"):
            order["state"] = "COMPLETED"

            # Predictive outcome learning (ML)
            if self.ml_engine:
                 self.ml_engine.train_from_ledger("delivery_efficiency", "execution.confirmed")

            self.shadow.commit("execution.confirmed", order_id, {
                "signal_type": signal["type"],
                "reality_check": "SUCCESS",
                "final_state": "COMPLETED"
            })

            if self.event_bus:
                self.event_bus.publish("iluvia.execution.completed", {
                    "order_id": order_id,
                    "signal": signal["type"]
                })
            return True

        raise ValueError(f"REALITY MISMATCH: digital order type {order['type']} != physical signal {signal['type']}")

    def _get_expected_signals(self, order_type: str):
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

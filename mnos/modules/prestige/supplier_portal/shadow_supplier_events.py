from typing import Dict, Any

class ShadowSupplierEvents:
    """
    Utility for standardizing supplier portal SHADOW events.
    """
    @staticmethod
    def contract_uploaded(supplier_id: str, resort_id: str, action_id: str):
        return {
            "event_type": "prestige.supplier.contract_uploaded",
            "supplier_id": supplier_id,
            "resort_id": resort_id,
            "action_id": action_id
        }

    @staticmethod
    def finance_approved(task_id: str, reviewer_id: str):
        return {
            "event_type": "prestige.supplier.finance_approved",
            "task_id": task_id,
            "reviewer_id": reviewer_id
        }

    @staticmethod
    def active_for_sale(action_id: str, resort_id: str):
        return {
            "event_type": "prestige.supplier.active_for_sale",
            "action_id": action_id,
            "resort_id": resort_id
        }

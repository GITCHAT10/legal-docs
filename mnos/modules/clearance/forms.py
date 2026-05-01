import uuid
from enum import Enum
from typing import Dict, List, Any, Optional

class DocumentStatus(Enum):
    REQUIRED = "required"
    UPLOADED = "uploaded"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUBMITTED_TO_AUTHORITY = "submitted_to_authority"
    APPROVED = "approved"

class UClearanceFormsPack:
    """
    U-Clearance Forms Pack: Registry of required documents for Customs and Port.
    """
    def __init__(self):
        # Master Registry
        self.doc_registry = {
            "commercial_invoice": {"authority": "CUSTOMS", "mandatory": True},
            "packing_list": {"authority": "CUSTOMS", "mandatory": True},
            "bill_of_lading": {"authority": "CUSTOMS", "mandatory": True},
            "airway_bill": {"authority": "CUSTOMS", "mandatory": True},
            "import_permit": {"authority": "CUSTOMS", "mandatory": False},
            "pre_valuation_form": {"authority": "CUSTOMS", "mandatory": False},
            "delivery_order": {"authority": "MPL", "mandatory": True},
            "mpl_invoice": {"authority": "MPL", "mandatory": True},
            "customs_payment_receipt": {"authority": "MPL", "mandatory": True}
        }

    def get_required_docs(self, shipment_type: str = "SEA"):
        # Simulated logic forSea cargo
        docs = ["commercial_invoice", "packing_list", "bill_of_lading", "delivery_order", "customs_payment_receipt", "mpl_invoice"]
        return {d: self.doc_registry[d] for d in docs}

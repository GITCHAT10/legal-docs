from typing import Dict, Any, List
from datetime import datetime
from mnos.modules.shadow.service import shadow
from mnos.modules.elegal.anchor import legal_anchor

class TenancyEngine:
    """
    Maldives Tenancy Jurisdiction Pack: Formalizing the rent economy.
    Manages leases, rent schedules, and legal compliance.
    """
    def __init__(self):
        self.leases: Dict[str, Dict[str, Any]] = {}

    def create_lease(self, landlord_id: str, tenant_id: str, property_id: str, monthly_rent: float, deposit: float) -> Dict[str, Any]:
        """
        Creates a legally-bound lease agreement in the eLEGAL kernel.
        """
        lease_id = f"LEASE-{datetime.now().strftime('%Y%m%d')}-{property_id[:4].upper()}"

        # Binding to Legal Anchor
        anchor_id = legal_anchor.create_anchor(contract_id=lease_id, actor_id=landlord_id)

        lease_data = {
            "lease_id": lease_id,
            "anchor_id": anchor_id,
            "landlord_id": landlord_id,
            "tenant_id": tenant_id,
            "property_id": property_id,
            "monthly_rent": monthly_rent,
            "deposit": deposit,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "rent_schedule": []
        }

        self.leases[lease_id] = lease_data
        shadow.commit("elegal.tenancy.lease_created", lease_data)
        return lease_data

    def get_lease(self, lease_id: str) -> Dict[str, Any]:
        if lease_id not in self.leases:
            raise ValueError(f"Lease {lease_id} not found.")
        return self.leases[lease_id]

tenancy_engine = TenancyEngine()

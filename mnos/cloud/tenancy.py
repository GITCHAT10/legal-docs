import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional

class TenantManager:
    """
    AIG AIR CLOUD: Multi-tenant Architecture Manager.
    Handles resort, government, and vendor isolation with AEGIS identity federation.
    """
    def __init__(self, identity_core, shadow):
        self.identity_core = identity_core
        self.shadow = shadow
        self.tenants = {} # tenant_id -> metadata

    def provision_tenant(self, actor_ctx: dict, name: str, tenant_type: str, island_id: str) -> dict:
        """
        Provision a new cloud tenant (Resort/Gov/Vendor).
        """
        tenant_id = f"TNT-{uuid.uuid4().hex[:8].upper()}"

        tenant_metadata = {
            "tenant_id": tenant_id,
            "name": name,
            "type": tenant_type, # RESORT, GOVERNMENT, VENDOR
            "island_id": island_id,
            "status": "PROVISIONING",
            "created_at": datetime.now(UTC).isoformat(),
            "data_isolation": "STRICT_SCHEMA_SILO"
        }

        self.tenants[tenant_id] = tenant_metadata

        # Log to SHADOW
        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.sovereign_context(trace_id=f"TNT-PROV-{tenant_id}"):
            self.shadow.commit("cloud.tenant.provisioned", actor_ctx.get("identity_id", "SYSTEM"), tenant_metadata)

        return tenant_metadata

    def get_tenant_context(self, tenant_id: str) -> Optional[dict]:
        return self.tenants.get(tenant_id)

    def federate_identity(self, tenant_id: str, external_user_data: dict) -> str:
        """
        Maps external tenant users to sovereign AEGIS identities.
        """
        if tenant_id not in self.tenants:
            raise ValueError("Invalid Tenant ID")

        # Standardize external user to AEGIS profile
        profile_data = {
            "full_name": external_user_data.get("name"),
            "profile_type": "tenant_user",
            "organization_id": tenant_id,
            "external_ref": external_user_data.get("external_id")
        }

        return self.identity_core.create_profile(profile_data)

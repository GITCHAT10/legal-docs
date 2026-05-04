from fastapi import APIRouter
from mnos.schemas.policy import PolicyMetadataSchema
from datetime import datetime, timezone

router = APIRouter(prefix="/mnos/v1")

@router.get("/policies/skyfarm", response_model=PolicyMetadataSchema)
async def get_skyfarm_policies():
    return {
        "policy_version": "v1.0.0",
        "active_rules": ["rule_default_allow", "rule_maldives_compliance"],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

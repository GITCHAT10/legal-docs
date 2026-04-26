from mnos.modules.shadow import service as shadow_service
from sqlalchemy.orm import Session

def commit_evidence(db: Session, trace_id: str, actor: str, action: str, entity_type: str, entity_id: str, payload: dict):
    """
    United Transfer Link to MNOS Core SHADOW Service.
    Ensures unified audit trail.
    """
    shadow_payload = {
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload
    }
    return shadow_service.commit_evidence(db, trace_id, shadow_payload)

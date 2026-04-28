from mnos.modules.shadow import service as shadow_service
def commit_shadow_evidence(db, trace_id, event, payload):
    shadow_payload = {
        "action": event,
        "payload": payload
    }
    return shadow_service.commit_evidence(db, trace_id, shadow_payload)

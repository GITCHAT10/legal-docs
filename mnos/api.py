from mnos.core.security.aegis import aegis
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events
from mnos.shared.execution_guard import guard

# --- SOVEREIGN AUTHORITY PLANE API ---
# Stable entry points for external consumption (UT,Standalone systems)

def verify_session(session_context):
    """AEGIS: Hardware-bound session verification."""
    return aegis.validate_session(session_context)

def preauthorize(folio_id, amount, credit_limit):
    """FCE: Financial pre-authorization gate."""
    return fce.validate_pre_auth(folio_id, amount, credit_limit)

def calculate_folio(base_amount, pax=1, nights=1, stay_hours=24.0, is_child=False, effective_tgst=None):
    """FCE: MIRA-compliant fiscal calculation."""
    return fce.calculate_folio(base_amount, pax, nights, stay_hours, is_child, effective_tgst)

def commit_evidence(event_type, payload):
    """SHADOW: Immutable audit commit. MUST be called via ExecutionGuard in prod."""
    return shadow.commit(event_type, payload)

def publish_event(event_type, data, trace_id=None):
    """EVENTS: Sovereign orchestration hub."""
    return events.publish(event_type, data, trace_id)

def execute_sovereign(action_type, payload, session_context, logic, financial_validation=False):
    """GUARD: Mandatory execution sequence (AEGIS -> FCE -> EXEC -> SHADOW -> EVENT)."""
    return guard.execute_sovereign_action(action_type, payload, session_context, logic, financial_validation)

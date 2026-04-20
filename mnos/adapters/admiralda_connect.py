from typing import Dict, Any, Optional
import uuid
from mnos.shared.sdk.mnos_client import mnos_client
from mnos.modules.fce import service as fce_service
from mnos.core.db import session as db_session

class AdmiraldaConnect:
    """
    MNOS Adapter for ADMIRALDA PBX: The Sovereign Integration Layer (Hardened).
    """
    def verify_voice_identity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            voiceprint_match = data.get("voiceprint_match", 0.0)
            is_verified = voiceprint_match >= 0.95
            return {
                "status": "VERIFIED" if is_verified else "UNVERIFIED",
                "persona": data.get("voiceprint_id"),
                "match_confidence": voiceprint_match
            }
        except Exception:
            return {"status": "FAILED", "detail": "AEGIS_UNREACHABLE"}

    def preauthorize_buffer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        REAL FCE Execution: Open Folio for goodwill buffer.
        """
        db = db_session.SessionLocal()
        try:
            # Enforce policy
            ltv = data.get("ltv", 0)
            risk = data.get("risk_of_churn", 0)
            if not (ltv > 10000 and risk > 0.5):
                return {"status": "DENIED", "reason": "POLICY_VIOLATION"}

            trace_id = f"FCE-BUF-{uuid.uuid4().hex}"
            folio = fce_service.open_folio(db, str(f"BUFF-{data.get('tenant_id')}"), trace_id)
            return {
                "status": "AUTHORIZED",
                "amount": data.get("requested_buffer"),
                "folio_id": folio.id,
                "trace_id": trace_id
            }
        except Exception as e:
            print(f"ADAPTER ERROR: {str(e)}")
            return {"status": "FAILED", "detail": str(e)}
        finally:
            db.close()

    def seal_evidence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            payload = {
                "audio_hash": data.get("audio_hash"),
                "transcript_hash": data.get("transcript_hash"),
                "envelope_hash": data.get("envelope_hash"),
                "intent_score": data.get("intent_score"),
                "consent_confirmed": data.get("consent_confirmed", False),
                "jurisdiction": data.get("jurisdiction", "Maldives"),
                "verification_method": data.get("verification_method", "VOICE_BIOMETRIC"),
                "execution_status": data.get("execution_status", "UNKNOWN")
            }
            trace_id = data.get("trace_id", f"SHADOW-{uuid.uuid4().hex}")
            shadow_resp = mnos_client.commit_evidence(trace_id, payload)
            return {
                "shadow_id": shadow_resp["id"],
                "shadow_signature": shadow_resp["hash"],
                "status": "SEALED"
            }
        except Exception as e:
            print(f"ADAPTER ERROR: {str(e)}")
            return {"status": "FAILED", "detail": str(e)}

admiralda_connect = AdmiraldaConnect()

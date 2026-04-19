from typing import Dict, Any
import os

class MnosClient:
    """
    Mock SDK for MNOS inter-module communication.
    In a real system, this would use HTTP calls to the respective services.
    """
    def commit_booking(self, data: Dict, trace_id: str) -> Dict:
        # Authority: MNOS CORE -> INN
        # This would normally be a POST to /mnos/core/bookings
        return {"reservation_id": f"RES-{trace_id[-8:]}", "status": "CONFIRMED"}

    def open_folio(self, reservation_id: str, trace_id: str) -> Dict:
        # Authority: FCE
        from mnos.modules.fce import service as fce_service
        from mnos.core.db.session import SessionLocal
        db = SessionLocal()
        try:
            folio = fce_service.open_folio(db, reservation_id, trace_id)
            return {"id": folio.id, "status": folio.status}
        finally:
            db.close()

    def commit_evidence(self, trace_id: str, payload: Dict) -> Dict:
        # Authority: SHADOW
        from mnos.modules.shadow import service as shadow_service
        from mnos.core.db.session import SessionLocal
        db = SessionLocal()
        try:
            evidence = shadow_service.commit_evidence(db, trace_id, payload)
            return {"id": evidence.id, "hash": evidence.current_hash}
        finally:
            db.close()

mnos_client = MnosClient()

from typing import Dict, Any, Optional
import os

class MnosClient:
    """
    SDK for MNOS inter-module communication.
    Authority is always delegated to the respective module service.
    """
    def commit_booking(self, data: Dict, trace_id: str) -> Dict:
        self.commit_evidence(trace_id, {"action": "BOOKING_COMMIT", "payload": data})
        return {"reservation_id": f"RES-{trace_id[-8:]}", "status": "CONFIRMED"}

    def open_folio(self, reservation_id: str, trace_id: str) -> Dict:
        from mnos.modules.fce import service as fce_service
        from mnos.core.db.session import SessionLocal
        db = SessionLocal()
        try:
            folio = fce_service.open_folio(db, reservation_id, trace_id)
            self.commit_evidence(trace_id, {
                "action": "FOLIO_OPEN",
                "entity_type": "FOLIO",
                "entity_id": folio.id,
                "after_state": {"status": folio.status}
            })
            return {"id": folio.id, "status": folio.status, "trace_id": folio.trace_id}
        finally:
            db.close()

    def commit_evidence(self, trace_id: str, payload: Dict) -> Dict:
        from mnos.modules.shadow import service as shadow_service
        from mnos.core.db.session import SessionLocal
        db = SessionLocal()
        try:
            evidence = shadow_service.commit_evidence(db, trace_id, payload)
            return {"id": evidence.id, "hash": evidence.current_hash}
        finally:
            db.close()

    def post_charge(self, folio_id: int, charge_data: Dict, trace_id: str) -> Dict:
        from mnos.modules.fce import service as fce_service
        from mnos.core.db.session import SessionLocal
        db = SessionLocal()
        try:
            line = fce_service.post_charge(db, folio_id, charge_data, trace_id)
            self.commit_evidence(trace_id, {
                "action": "CHARGE_POST",
                "entity_type": "FOLIO_LINE",
                "entity_id": line.id,
                "after_state": {"amount": line.amount}
            })
            return {"id": line.id, "amount": line.amount, "trace_id": line.trace_id}
        finally:
            db.close()

mnos_client = MnosClient()

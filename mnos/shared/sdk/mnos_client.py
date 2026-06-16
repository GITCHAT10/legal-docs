from typing import Dict, Any, Optional
import os
from sqlalchemy.orm import Session

class MnosClient:
    """
    Authoritative SDK for MNOS inter-module communication.
    Ensures every cross-module action is evidence-locked in SHADOW.
    """

    def _get_db(self):
        from mnos.core.db.session import SessionLocal
        return SessionLocal()

    def commit_evidence(self, trace_id: str, payload: Dict, actor: str = "SYSTEM") -> Dict:
        from mnos.core.shadow import service as shadow_service
        db = self._get_db()
        try:
            # SHADOW evidence is the root of law in MNOS
            evidence = shadow_service.commit_evidence(db, trace_id, payload)
            return {"id": evidence.id, "hash": evidence.current_hash, "trace_id": trace_id}
        finally:
            db.close()

    def open_folio(self, reservation_id: str, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> Dict:
        from mnos.core.fce import service as fce_service
        db = self._get_db()
        try:
            # Delegate to FCE service which already handles SHADOW commit
            folio = fce_service.open_folio(db, reservation_id, trace_id, tenant_id, actor)
            return {"id": folio.id, "status": folio.status, "trace_id": folio.trace_id}
        finally:
            db.close()

    def post_charge(self, folio_id: int, charge_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> Dict:
        from mnos.core.fce import service as fce_service
        db = self._get_db()
        try:
            line = fce_service.post_charge(db, folio_id, charge_data, trace_id, tenant_id, actor)
            return {"id": line.id, "amount": line.amount, "trace_id": line.trace_id}
        finally:
            db.close()

    def post_transaction(self, folio_id: int, transaction_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> Dict:
        from mnos.core.fce import service as fce_service
        db = self._get_db()
        try:
            tx = fce_service.post_transaction(db, folio_id, transaction_data, trace_id, tenant_id, actor)
            return {"id": tx.id, "amount": tx.amount, "status": tx.status}
        finally:
            db.close()

    def create_transfer_request(self, transfer_data: Dict, trace_id: str, tenant_id: str = "default", actor: str = "SYSTEM") -> Dict:
        from mnos.modules.aqua.transfers import service as aqua_service
        from mnos.modules.aqua.transfers.schemas import TransferRequestCreate
        db = self._get_db()
        try:
            # Convert dict to schema
            req_in = TransferRequestCreate(**transfer_data, trace_id=trace_id, tenant_id=tenant_id)
            req = aqua_service.create_transfer_request(db, request_in=req_in, actor=actor)
            return {"id": req.id, "status": req.status, "trace_id": req.trace_id}
        finally:
            db.close()

mnos_client = MnosClient()

from typing import List, Any
from sqlalchemy.orm import Session
from mnos.modules.fce import models, service
from mnos.modules.shadow import service as shadow_service
import uuid

def split_bundle_contract(db: Session, folio_id: int, line_ids: List[int], target_reservation_id: str, trace_id: str, actor: str = "SYSTEM"):
    """
    Bundle Integrity Engine: Splits a contract and issues credits if integrity is compromised.
    """
    try:
        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio: raise ValueError("Folio not found")

        # 1. Create target folio for split
        target_folio = service.open_folio(db, target_reservation_id, f"SPLIT-{trace_id}", actor=actor)

        total_moved = 0.0
        for lid in line_ids:
            line = db.query(models.FolioLine).filter(models.FolioLine.id == lid, models.FolioLine.folio_id == folio_id).first()
            if line:
                before_state = {"folio_id": folio_id}
                line.folio_id = target_folio.id
                total_moved += line.amount

                # Audit the move
                shadow_service.commit_evidence(db, f"MOVE-{uuid.uuid4().hex[:4]}", {
                    "actor": actor,
                    "action": "BUNDLE_LINE_MOVE",
                    "entity_type": "FOLIO_LINE",
                    "entity_id": line.id,
                    "before_state": before_state,
                    "after_state": {"folio_id": target_folio.id}
                })

        folio.total_amount -= total_moved
        target_folio.total_amount = total_moved

        db.commit()
        return target_folio
    except Exception:
        db.rollback()
        raise

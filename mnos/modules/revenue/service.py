from typing import Dict, Any, List
from sqlalchemy.orm import Session
from mnos.modules.revenue import models
from mnos.core.fce.models import FolioLine
from mnos.core.shadow import service as shadow_service
import uuid

def calculate_distribution(db: Session, line_id: int, contract_id: int, trace_id: str, actor: str = "SYSTEM") -> models.RevenueSplit:
    """
    Revenue Engine Execution.
    Sale -> Distribution -> Finality.
    """
    try:
        line = db.query(FolioLine).filter(FolioLine.id == line_id).first()
        contract = db.query(models.PartnerContract).filter(models.PartnerContract.id == contract_id).first()

        if not line or not contract:
            raise ValueError("Line or Contract not found")

        # 1. Split calculation (Net of tax vs Gross depends on contract)
        # Here we split the base amount
        partner_share = line.base_amount * (contract.share_percentage / 100.0)
        resort_share = line.base_amount - partner_share

        # 2. Record Distribution Authority
        split = models.RevenueSplit(
            trace_id=trace_id,
            line_id=line_id,
            contract_id=contract_id,
            partner_amount=partner_share,
            resort_amount=resort_share,
            tax_allocation={
                "line_sc": line.service_charge,
                "line_tgst": line.tgst
            }
        )
        db.add(split)
        db.flush()

        # 3. Verifiable trace
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor,
            "action": "REVENUE_DISTRIBUTION",
            "entity_type": "REVENUE_SPLIT",
            "entity_id": split.id,
            "after_state": {
                "partner_amount": partner_share,
                "resort_amount": resort_share,
                "contract_id": contract_id
            }
        })

        db.commit()
        db.refresh(split)
        return split
    except Exception:
        db.rollback()
        raise

def create_partner_contract(db: Session, data: Dict, trace_id: str) -> models.PartnerContract:
    contract = models.PartnerContract(
        trace_id=trace_id,
        **data
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

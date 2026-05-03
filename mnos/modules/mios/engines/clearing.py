from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Dict, Optional
from mnos.modules.mios.schemas.models import ClearingRecord

class SkyClearingEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.records: Dict[UUID, ClearingRecord] = {}

    def create_record(self, actor_ctx: dict, shipment_id: UUID, invoice_no: str, total_usd: Decimal) -> ClearingRecord:
        record_id = uuid4()
        record = ClearingRecord(
            id=record_id,
            shipment_id=shipment_id,
            invoice_no=invoice_no,
            invoice_total_usd=total_usd
        )
        self.records[shipment_id] = record
        self.shadow.commit("mios.clearing.record_created", actor_ctx["identity_id"], record.dict())
        return record

    def validate_orca(self, shipment_id: UUID) -> dict:
        record = self.records.get(shipment_id)
        if not record:
            return {"passed": False, "reason": "No clearing record found"}

        results = {
            "INV_MATH_001": record.invoice_verified,
            "HS_PRODUCT_001": record.hs_code_confirmed,
            "CROSS_DOC_001": record.invoice_verified and record.hs_code_confirmed
        }

        passed = all(results.values())
        return {"passed": passed, "results": results}

    def submit_to_customs(self, actor_ctx: dict, shipment_id: UUID, declaration_no: str):
        orca = self.validate_orca(shipment_id)
        if not orca["passed"]:
            details = orca.get("results") or orca.get("reason") or "Unknown ORCA validation failure"
            raise ValueError(f"ORCA validation failed: {details}")

        record = self.records.get(shipment_id)
        record.declaration_no = declaration_no
        record.status = "SUBMITTED_TO_CUSTOMS"
        self.shadow.commit("mios.clearing.submitted", actor_ctx["identity_id"], {"shipment_id": str(shipment_id), "declaration_no": declaration_no})

    def match_payment(self, actor_ctx: dict, shipment_id: UUID, assessment_no: str, receipt_no: str):
        record = self.records.get(shipment_id)
        if not record or not record.declaration_no:
            raise ValueError("No active Customs declaration found")

        record.assessment_no = assessment_no
        record.customs_payment_matched = True
        record.status = "CUSTOMS_PAID"
        self.shadow.commit("mios.clearing.payment_matched", actor_ctx["identity_id"], {"shipment_id": str(shipment_id), "receipt_no": receipt_no})

    def verify_port_release(self, actor_ctx: dict, shipment_id: UUID):
        record = self.records.get(shipment_id)
        if not record.customs_payment_matched:
            raise ValueError("Customs payment not matched")

        record.port_release_verified = True
        record.status = "RELEASED_FROM_PORT"
        self.shadow.commit("mios.clearing.port_released", actor_ctx["identity_id"], {"shipment_id": str(shipment_id)})

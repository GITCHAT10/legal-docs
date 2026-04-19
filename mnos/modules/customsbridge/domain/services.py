import uuid
import logging
from sqlalchemy.orm import Session
from mnos.modules.customsbridge.app.config import settings
from mnos.modules.customsbridge.adapters.mnos_clients import (
    AquaClient, OdysseyClient, FceClient, EleoneClient,
    EventsClient, ShadowClient, AegisClient, SkyGodownClient
)
from mnos.modules.customsbridge.schemas.request import ClearanceRequest, OverrideRequest, InspectionResult
from mnos.modules.customsbridge.schemas.response import ClearanceResponse
from mnos.modules.customsbridge.domain.models import CustomsClearanceRequest, CustomsClearanceBatch, CustomsReview

logger = logging.getLogger(__name__)

class CustomsOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.aqua = AquaClient(settings.AQUA_URL)
        self.odyssey = OdysseyClient(settings.ODYSSEY_URL)
        self.fce = FceClient(settings.FCE_URL)
        self.eleone = EleoneClient(settings.ELEONE_URL)
        self.events = EventsClient(settings.EVENTS_URL)
        self.shadow = ShadowClient(settings.SHADOW_URL)
        self.aegis = AegisClient(settings.AEGIS_URL)
        self.skygodown = SkyGodownClient(settings.SKYGODOWN_URL)

    async def _safe_call(self, func, *args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"External service call failed: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    async def process_clearance_request(self, request_in: ClearanceRequest) -> ClearanceResponse:
        reasons = []
        status = "APPROVED"
        code = 200
        integrity_status = "VERIFIED"
        next_action = "RELEASE"
        aegis_action = None

        # 1. Receive request - Log to SHADOW/EVENTS
        await self._safe_call(self.shadow.write_record, {"event": "CUSTOMS_CLEARANCE_REQUESTED", "data": request_in.model_dump()})
        await self._safe_call(self.events.publish_event, "CUSTOMS_CLEARANCE_REQUESTED", request_in.model_dump())

        # 2. Verify BatchIDs with AQUA
        aqua_res = await self._safe_call(self.aqua.verify_batches, request_in.mnos_batch_ids)
        provenance_status = "VERIFIED"
        if aqua_res.get("status") != "VERIFIED":
            reasons.append("BatchID not found or unverified")
            status = "BLOCKED"
            provenance_status = "FAILED"
        else:
            await self._safe_call(self.events.publish_event, "CUSTOMS_PROVENANCE_VERIFIED", {"request_id": request_in.request_id})

        # 3. Validate yield/weight with ODYSSEY
        odyssey_res = await self._safe_call(self.odyssey.validate_yield, request_in.mnos_batch_ids, request_in.declared_weight)
        yield_status = "MATCH"
        if odyssey_res.get("status") == "MISMATCH":
            reasons.append("Weight variance above soft threshold")
            yield_status = "MISMATCH"
            if status != "BLOCKED":
                status = "REVIEW"
            await self._safe_call(self.events.publish_event, "CUSTOMS_YIELD_MISMATCH_DETECTED", {"request_id": request_in.request_id})

        # 4. Check export readiness with SKYGODOWN
        skygodown_res = await self._safe_call(self.skygodown.check_export_readiness, request_in.mnos_batch_ids)
        if skygodown_res.get("status") != "READY":
            reasons.append("Export readiness check failed in SKYGODOWN")
            if status == "APPROVED":
                status = "REVIEW"

        # 5. Confirm commission/settlement with FCE
        fce_res = await self._safe_call(self.fce.check_settlement, request_in.mnos_batch_ids)
        settlement_status = "SETTLED"
        if fce_res.get("status") != "SETTLED":
            reasons.append("Settlement incomplete")
            settlement_status = "PENDING"
            status = "BLOCKED"
            await self._safe_call(self.events.publish_event, "CUSTOMS_SETTLEMENT_INCOMPLETE", {"request_id": request_in.request_id})

        # 6. Score anomaly via ELEONE
        eleone_res = await self._safe_call(self.eleone.get_risk_score, request_in.model_dump())
        if not eleone_res or "risk_score" not in eleone_res:
            await self._safe_call(
                self.shadow.write_record,
                {
                    "event": "CUSTOMS_FAILURE",
                    "data": {
                        "reason": "ELEONE risk scoring unavailable",
                        "request": request_in.model_dump()
                    }
                }
            )

            logger.warning(
                "ELEONE unavailable - forcing REVIEW",
                extra={"request": request_in.model_dump()}
            )

            return ClearanceResponse(
                status="REVIEW",
                code=202,
                integrity_status="MANUAL_REVIEW_REQUIRED",
                risk_score=0.0,
                next_action="SUPERVISOR_REVIEW",
                reasons=["ELEONE risk scoring unavailable"]
            )

        risk_score = eleone_res["risk_score"]

        if risk_score > 0.9:
            status = "BLOCKED"
            reasons.append("High risk score from ELEONE")
            logger.warning(f"High risk score detected: {risk_score} for request {request_in.request_id}")
        elif risk_score > 0.4 and status == "APPROVED":
            status = "REVIEW"
            logger.info(f"Moderate risk score detected: {risk_score} for request {request_in.request_id}, forcing REVIEW")

        # Final adjustments for BLOCKED/REVIEW
        if status == "BLOCKED":
            code = 403
            integrity_status = "FAILED"
            next_action = "PHYSICAL_INSPECTION"
            aegis_res = await self._safe_call(self.aegis.trigger_port_lock, request_in.container_id, ", ".join(reasons), request_in.request_id)
            aegis_action = "PORT_LOCK_ENGAGED" if not aegis_res.get("simulated") else "PORT_LOCK_SIMULATED"
            await self._safe_call(self.events.publish_event, "CUSTOMS_CLEARANCE_BLOCKED", {"request_id": request_in.request_id, "reasons": reasons})
        elif status == "REVIEW":
            code = 202
            integrity_status = "MANUAL_REVIEW_REQUIRED"
            next_action = "SUPERVISOR_REVIEW"
            await self._safe_call(self.events.publish_event, "CUSTOMS_REVIEW_REQUIRED", {"request_id": request_in.request_id})
        else:
            await self._safe_call(self.events.publish_event, "CUSTOMS_CLEARANCE_APPROVED", {"request_id": request_in.request_id})

        # DB Persistence
        db_request = CustomsClearanceRequest(
            request_id=request_in.request_id,
            container_id=request_in.container_id,
            declaration_type=request_in.declaration_type,
            commodity=request_in.commodity,
            origin_site_id=request_in.origin_site_id,
            declared_weight=request_in.declared_weight,
            destination_country=request_in.destination_country,
            requested_by_officer_id=request_in.requested_by_officer_id,
            status=status,
            risk_score=risk_score,
            clearance_token=str(uuid.uuid4()) if status == "APPROVED" else None
        )
        self.db.add(db_request)
        self.db.flush()

        for batch_id in request_in.mnos_batch_ids:
            db_batch = CustomsClearanceBatch(
                clearance_request_id=db_request.id,
                batch_id=batch_id,
                provenance_status=provenance_status,
                yield_status=yield_status,
                settlement_status=settlement_status
            )
            self.db.add(db_batch)

        if status == "REVIEW":
            db_review = CustomsReview(
                clearance_request_id=db_request.id,
                review_status="PENDING"
            )
            self.db.add(db_review)

        self.db.commit()

        # SHADOW Commit
        decision_data = {
            "request_id": request_in.request_id,
            "status": status,
            "reasons": reasons,
            "risk_score": risk_score,
            "aegis_action": aegis_action
        }
        await self._safe_call(self.shadow.write_record, {"event": "CUSTOMS_DECISION_FINALIZED", "data": decision_data})

        return ClearanceResponse(
            status=status,
            code=code,
            clearance_token=db_request.clearance_token,
            integrity_status=integrity_status,
            risk_score=float(risk_score),
            next_action=next_action,
            reasons=reasons if reasons else None,
            aegis_action=aegis_action
        )

    def get_request_by_id(self, request_id: str):
        return self.db.query(CustomsClearanceRequest).filter(CustomsClearanceRequest.request_id == request_id).first()

    async def process_override(self, request_in: OverrideRequest):
        # Dual authorization logic: supervisor_id and officer_id must be present (handled by schema)
        # In a more advanced implementation, we would verify their roles
        review = self.db.query(CustomsReview).filter(CustomsReview.id == request_in.review_id).first()
        if not review:
            await self._safe_call(
                self.shadow.write_record,
                {
                    "event": "CUSTOMS_FAILURE",
                    "data": {
                        "reason": "Override attempted for unknown review_id",
                        "review_id": request_in.review_id
                    }
                }
            )
            logger.warning(
                "Override completion blocked for unknown review_id",
                extra={"review_id": request_in.review_id}
            )
            return {"status": "FAILED", "reason": "Review not found", "action": "NO_EVENT_EMITTED"}

        review.review_status = "OVERRIDDEN"
        review.reviewer_id = f"{request_in.officer_id}/{request_in.supervisor_id}"
        review.decision_notes = request_in.reason

        # Update associated request
        req = self.db.query(CustomsClearanceRequest).filter(CustomsClearanceRequest.id == review.clearance_request_id).first()
        if req:
            req.status = "APPROVED"
            req.clearance_token = str(uuid.uuid4())

        self.db.commit()

        await self._safe_call(self.shadow.write_record, {"event": "CUSTOMS_OVERRIDE_EXECUTED", "data": request_in.model_dump()})
        await self._safe_call(self.events.publish_event, "CUSTOMS_OVERRIDE_EXECUTED", request_in.model_dump())
        return {"status": "APPROVED", "message": "Supervisor dual-authorized override successful"}

    async def process_inspection(self, result: InspectionResult):
        db_request = self.get_request_by_id(result.request_id)
        if not db_request:
            await self._safe_call(
                self.shadow.write_record,
                {
                    "event": "CUSTOMS_FAILURE",
                    "data": {
                        "reason": "Inspection attempted for unknown request_id",
                        "request_id": result.request_id
                    }
                }
            )

            logger.warning(
                "Inspection completion blocked for unknown request_id",
                extra={"request_id": result.request_id}
            )

            return {
                "status": "FAILED",
                "reason": "Request not found",
                "action": "NO_EVENT_EMITTED"
            }

        db_request.status = "INSPECTED_" + result.inspection_result
        self.db.commit()

        await self._safe_call(self.shadow.write_record, {"event": "CUSTOMS_INSPECTION_COMPLETED", "data": result.model_dump()})
        await self._safe_call(self.events.publish_event, "CUSTOMS_INSPECTION_COMPLETED", result.model_dump())
        return {"status": "SUCCESS", "message": "Inspection result recorded"}

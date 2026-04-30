from fastapi import APIRouter, Depends
from mnos.modules.prestige.forms.uhnw_booking_template import UHNWBookingTemplate
from mnos.modules.prestige.workflows.intake_validation import IntakeValidation

def create_uhnw_router(core, validator: IntakeValidation, get_actor_ctx):
    router = APIRouter(prefix="/uhnw", tags=["prestige_uhnw"])

    @router.post("/intake")
    async def process_intake(data: UHNWBookingTemplate, actor: dict = Depends(get_actor_ctx)):
        valid, msg = validator.validate_completion(data)
        needs_esc = validator.check_escalation(data)

        status = "COMPLETED" if valid else "INCOMPLETE"
        if needs_esc: status = "HUMAN_ESCALATION_REQUIRED"

        return {
            "status": status,
            "validation_message": msg,
            "escalation_required": needs_esc
        }

    return router

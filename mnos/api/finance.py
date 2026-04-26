from fastapi import APIRouter, Depends

def create_finance_router(fce_hardened, get_actor_ctx):
    router = APIRouter(prefix="/finance", tags=["finance"])

    @router.post("/payouts/release")
    async def release_payout(milestone: str, ref_id: str, total_amount: float, actor: dict = Depends(get_actor_ctx)):
        from mnos.shared.execution_guard import _sovereign_context
        import uuid
        # MANUALLY WRAP IN SOVEREIGN CONTEXT SINCE FCE_HARDENED IS LEGACY COMPONENT
        token = _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})
        try:
            escrow_id = fce_hardened.create_escrow(actor["identity_id"], total_amount, ref_id)
            release_amt = fce_hardened.release_milestone(actor["identity_id"], escrow_id, 10 if milestone == "AWARD" else 0)
            return {"release_amount": release_amt, "status": "RELEASED"}
        finally:
            _sovereign_context.set(None)

    @router.post("/installment")
    async def create_installment(total: float, months: int, actor: dict = Depends(get_actor_ctx)):
        from main import fce_core
        return fce_core.calculate_installment_plan(total, months)

    return router

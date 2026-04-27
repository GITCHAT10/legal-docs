from fastapi import APIRouter, Depends, HTTPException

def create_finance_router(fce_hardened, mira_bridge, get_actor_ctx):
    router = APIRouter(tags=["finance"])

    @router.post("/payouts/release")
    async def release_payout(milestone: str, ref_id: str, total_amount: float, actor: dict = Depends(get_actor_ctx)):
        from mnos.shared.execution_guard import ExecutionGuard
        # MANUALLY WRAP IN SOVEREIGN CONTEXT SINCE FCE_HARDENED IS LEGACY COMPONENT
        with ExecutionGuard.sovereign_context(actor=actor, trace_id=f"PAY-{ref_id}"):
            escrow_id = fce_hardened.create_escrow(actor["identity_id"], total_amount, ref_id)
            release_amt = fce_hardened.release_milestone(actor["identity_id"], escrow_id, 10 if milestone == "AWARD" else 0)
            return {"release_amount": release_amt, "status": "RELEASED"}

    @router.post("/installment")
    async def create_installment(total: float, months: int, actor: dict = Depends(get_actor_ctx)):
        plan = {
            "total": total,
            "months": months,
            "monthly": round(total / months, 2),
            "status": "ACTIVE"
        }
        return plan

    @router.get("/mira/daily-report")
    async def get_mira_report(vendor_id: str = None, date: str = None, actor: dict = Depends(get_actor_ctx)):
        """MIRA-Bridge: Fetch daily tax aggregation."""
        return mira_bridge.get_daily_report(vendor_id, date)

    @router.get("/mira/invoice/{order_id}")
    async def get_mira_invoice(order_id: str, actor: dict = Depends(get_actor_ctx)):
        """MIRA-Bridge: Fetch MIRA-compliant invoice."""
        invoice = mira_bridge.invoices.get(order_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    return router

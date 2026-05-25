import uuid
from typing import Dict, Any, List, Optional
from mnos.modules.imoxon.supplier.rate_models import (
    ChannelType, VisibilityScope, MarketSellingRate, RateApprovalStatus
)
from mnos.shared.exceptions import ExecutionValidationError

class PHRateEngine:
    """
    PH Supplier Portal Rate Engine: Governing layer for rate intake, approval, and channel distribution.
    Enforces MAC EOS Sovereignty and SHADOW audit seals.
    """
    def __init__(self, guard, shadow, events, fce):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.fce = fce
        self.rates: Dict[str, MarketSellingRate] = {}

    def intake_contract_rate(self, actor_ctx: dict, payload: dict) -> MarketSellingRate:
        """
        Supplier submits a new rate contract. Starts in DRAFT/SUBMITTED state.
        """
        def _execute_intake():
            rate_id = f"RATE-{uuid.uuid4().hex[:8].upper()}"

            # Basic validation
            if payload.get("base_net_rate", 0) <= 0:
                raise ExecutionValidationError("FAIL_CLOSED: Base net rate must be positive")

            rate = MarketSellingRate(
                rate_id=rate_id,
                supplier_id=payload["supplier_id"],
                product_id=payload["product_id"],
                channel_type=payload["channel_type"],
                visibility_scope=payload.get("visibility_scope", VisibilityScope.PRIVATE),
                base_net_rate=payload["base_net_rate"],
                public_rate=payload.get("public_rate", payload["base_net_rate"] * 1.3),
                b2b_agent_net_rate=payload.get("b2b_agent_net_rate", payload["base_net_rate"] * 1.1),
                b2b_agent_commission_rate=payload.get("b2b_agent_commission_rate", 0.1),
                b2b2c_guest_rate=payload.get("b2b2c_guest_rate", payload["base_net_rate"] * 1.25),
                corporate_rate=payload.get("corporate_rate", payload["base_net_rate"] * 1.15),
                government_rate=payload.get("government_rate", payload["base_net_rate"] * 1.1),
                vip_private_rate=payload.get("vip_private_rate", payload["base_net_rate"] * 1.5),
                black_book_rate=payload.get("black_book_rate", payload["base_net_rate"] * 2.0),
                ota_public_rate=payload.get("ota_public_rate", payload["base_net_rate"] * 1.4),
                package_rate=payload.get("package_rate", payload["base_net_rate"] * 1.2),
                room_plus_transfer_rate=payload.get("room_plus_transfer_rate", payload["base_net_rate"] * 1.25),
                room_plus_experience_rate=payload.get("room_plus_experience_rate", payload["base_net_rate"] * 1.3),
                approval_status=RateApprovalStatus.SUBMITTED
            )

            self.rates[rate_id] = rate
            self.events.publish("rate.intake.submitted", rate.model_dump())
            return rate.model_dump()

        return self.guard.execute_sovereign_action(
            "rate.intake",
            actor_ctx,
            _execute_intake
        )

    def approve_rate(self, actor_ctx: dict, rate_id: str, stage: str):
        """
        Governs the multi-stage approval flow: FINANCE -> REVENUE -> CMO.
        """
        rate = self.rates.get(rate_id)
        if not rate:
            raise ExecutionValidationError(f"RATE_NOT_FOUND: {rate_id}")

        def _execute_approval():
            role = actor_ctx.get("role")

            if stage == "FINANCE":
                if role not in ["finance_reviewer", "mac_eos_admin"]:
                    raise PermissionError("UNAUTHORIZED: Finance approval requires finance_reviewer role")
                rate.approval_status = RateApprovalStatus.FINANCE_APPROVED

            elif stage == "REVENUE":
                if rate.approval_status != RateApprovalStatus.FINANCE_APPROVED:
                    raise ExecutionValidationError("FLOW_VIOLATION: Revenue approval requires Finance approval first")
                if role not in ["revenue_reviewer", "mac_eos_admin"]:
                    raise PermissionError("UNAUTHORIZED: Revenue approval requires revenue_reviewer role")
                rate.approval_status = RateApprovalStatus.REVENUE_APPROVED

            elif stage == "CMO":
                if rate.approval_status != RateApprovalStatus.REVENUE_APPROVED:
                    raise ExecutionValidationError("FLOW_VIOLATION: CMO approval requires Revenue approval first")
                if role not in ["cmo_reviewer", "mac_eos_admin"]:
                    raise PermissionError("UNAUTHORIZED: CMO approval requires cmo_reviewer role")

                # Check Channel Gates before final publish
                self._verify_channel_gates(rate)

                rate.approval_status = RateApprovalStatus.PUBLISHED
                rate.safe_to_publish = True

                # Seal the rate in SHADOW
                seal = self.shadow.commit("rate.audit_seal", actor_ctx.get("identity_id"), {
                    "rate_id": rate_id,
                    "final_status": "PUBLISHED",
                    "timestamp": "FORENSIC_SEALED"
                })
                rate.audit_seal = seal

            self.events.publish(f"rate.approval.{stage.lower()}", rate.model_dump())
            return rate.model_dump()

        return self.guard.execute_sovereign_action(
            f"rate.approve.{stage.lower()}",
            actor_ctx,
            _execute_approval
        )

    def _verify_channel_gates(self, rate: MarketSellingRate):
        """
        Enforce mandatory channel distribution rules.
        """
        # B2C Gate
        if rate.channel_type == ChannelType.B2C_DIRECT:
            if rate.visibility_scope != VisibilityScope.PUBLIC:
                 raise ExecutionValidationError("GATE_VIOLATION: B2C requires PUBLIC visibility")

        # B2B Gate
        if rate.channel_type == ChannelType.B2B_AGENT:
            # Metadata check for agent tiering would happen here
            pass

        # B2B2C Gate
        if rate.channel_type == ChannelType.B2B2C_AGENT_TO_GUEST:
            # Ensure guest rate > agent net rate (margin floor)
            if rate.b2b2c_guest_rate <= rate.b2b_agent_net_rate:
                raise ExecutionValidationError("GATE_VIOLATION: B2B2C guest rate must be higher than agent net rate")

        # B2G Gate
        if rate.channel_type == ChannelType.B2G_GOVERNMENT:
            if rate.visibility_scope not in [VisibilityScope.RESTRICTED, VisibilityScope.PRIVATE]:
                raise ExecutionValidationError("GATE_VIOLATION: B2G requires RESTRICTED or PRIVATE visibility")

        # VIP / Black Book Gate
        if rate.channel_type in [ChannelType.VIP_PRIVATE, ChannelType.BLACK_BOOK]:
            if rate.visibility_scope not in [VisibilityScope.P3_PRIVACY, VisibilityScope.P4_PRIVACY]:
                raise ExecutionValidationError(f"GATE_VIOLATION: {rate.channel_type} requires P3/P4 Privacy scope")

        # OTA Gate
        if rate.channel_type == ChannelType.OTA_PUBLIC:
            if rate.visibility_scope != VisibilityScope.PUBLIC:
                raise ExecutionValidationError("GATE_VIOLATION: OTA requires PUBLIC visibility")

    def get_market_selling_rate(self, channel: ChannelType, rate_id: str, actor_ctx: dict):
        """
        Retrieves the specific rate for a channel if authorized.
        """
        rate = self.rates.get(rate_id)
        if not rate or not rate.safe_to_publish:
             raise ExecutionValidationError("RATE_UNAVAILABLE: Rate not found or not published")

        # Role-based visibility scoping
        role = actor_ctx.get("role")

        # Black Book specific visibility
        if rate.channel_type == ChannelType.BLACK_BOOK:
            if role not in ["black_book_agent", "mac_eos_admin"]:
                raise PermissionError("UNAUTHORIZED: Black Book rates only visible to approved agents")

        # VIP specific visibility
        if rate.channel_type == ChannelType.VIP_PRIVATE:
            if role not in ["vip_concierge", "mac_eos_admin"]:
                raise PermissionError("UNAUTHORIZED: VIP rates only visible to VIP concierge")

        return rate.model_dump()

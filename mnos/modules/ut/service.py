from typing import Dict, Any, List
from mnos.shared.execution_guard import guard
from mnos.modules.aig_vault.service import aig_vault
from mnos.modules.fce.service import fce
from mnos.infrastructure.mig_event_spine.service import events
from decimal import Decimal

class UnitedTransferService:
    """
    UNITED TRANSFER (Execution Layer): Standalone Transport & Cargo Service.
    Connects to MNOS Cloud Infrastructure via secure APIs.
    """
    def create_booking(self, booking_data: Dict[str, Any], session_context: Dict[str, Any], connection_context: Dict[str, Any]):
        """
        Creates a transport booking.
        Enforces: AIGAegis Identity -> AIG_TUNNEL Network -> NEXUS Authority (FCE) -> AIGShadow Audit.
        """
        def booking_logic(p):
            # 1. NEXUS Authority: Pre-authorize payment via FCE
            # Simulations of Standalone UT calling NEXUS Authority service
            amount = Decimal(p.get("amount", "0.00"))
            limit = Decimal(p.get("limit", "1000.00"))
            fce.validate_pre_auth(f"UT-{p['customer_id']}", amount, limit)

            # 2. Standalone UT logic
            booking_id = f"UT-{p['customer_id']}-101"

            # 3. Connect to AIGVault for manifest storage
            path = aig_vault.secure_storage_path(f"manifest_{booking_id}")

            return {"status": "BOOKED", "booking_id": booking_id, "manifest_path": path, "amount_authorized": str(amount)}

        return guard.execute_sovereign_action(
            action_type="ut.booking.created",
            payload=booking_data,
            session_context=session_context,
            execution_logic=booking_logic,
            connection_context=connection_context,
            financial_validation=True
        )

    def dispatch_cargo(self, cargo_id: str, session_context: Dict[str, Any], connection_context: Dict[str, Any], evidence: Dict[str, Any], approvals: List[str]):
        """
        Critical Cargo Dispatch: Requires L5 Governance Check.
        """
        def dispatch_logic(p):
            return {"status": "DISPATCHED", "cargo_id": p["cargo_id"]}

        return guard.execute_sovereign_action(
            action_type="ut.cargo.dispatch",
            payload={"cargo_id": cargo_id},
            session_context=session_context,
            execution_logic=dispatch_logic,
            connection_context=connection_context,
            governance_evidence=evidence,
            approvals=approvals
        )

    def finalize_payout(self, booking_id: str, amount: Decimal, session_context: Dict[str, Any], connection_context: Dict[str, Any]):
        """
        Finalizes payment and triggers payout via NEXUS FCE.
        """
        def payout_logic(p):
            # Finalize payment in FCE (Simulation)
            # In a real system, this would move funds from escrow to provider
            return {"status": "PAID", "booking_id": p["booking_id"], "amount": str(p["amount"])}

        return guard.execute_sovereign_action(
            action_type="ut.payout.finalized",
            payload={"booking_id": booking_id, "amount": amount},
            session_context=session_context,
            execution_logic=payout_logic,
            connection_context=connection_context,
            financial_validation=True
        )

ut_service = UnitedTransferService()

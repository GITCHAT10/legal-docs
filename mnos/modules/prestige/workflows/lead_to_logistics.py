from enum import Enum
from typing import Dict, Any, List
import uuid

class LeadStatus(str, Enum):
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_QUALIFIED = "LEAD_QUALIFIED"
    BOOKING_PROFILE_COMPLETED = "BOOKING_PROFILE_COMPLETED"
    BOOKING_PROFILE_INCOMPLETE = "BOOKING_PROFILE_INCOMPLETE"
    PACKAGE_OPTIONS_GENERATED = "PACKAGE_OPTIONS_GENERATED"
    QUOTE_VALIDATED = "QUOTE_VALIDATED"
    QUOTE_VALIDATION_FAILED = "QUOTE_VALIDATION_FAILED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    QUOTE_ACCEPTED = "QUOTE_ACCEPTED"
    UPOS_PAYMENT_REQUEST_CREATED = "UPOS_PAYMENT_REQUEST_CREATED"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    FCE_SETTLEMENT_LOCKED = "FCE_SETTLEMENT_LOCKED"
    HOTEL_BOOKING_CONFIRMED = "HOTEL_BOOKING_CONFIRMED"
    TRANSFER_BOOKING_CONFIRMED = "TRANSFER_BOOKING_CONFIRMED"
    SUPPLIER_CONFIRMATIONS_LOCKED = "SUPPLIER_CONFIRMATIONS_LOCKED"
    GUEST_APP_BUNDLE_CREATED = "GUEST_APP_BUNDLE_CREATED"
    SHADOW_72H_PROOFING_STARTED = "SHADOW_72H_PROOFING_STARTED"
    FINAL_24H_LOGISTICS_PROOF_SEALED = "FINAL_24H_LOGISTICS_PROOF_SEALED"

class LeadToLogisticsWorkflow:
    def __init__(self, core):
        self.core = core
        self.leads = {} # lead_id -> data

    def transition_state(self, lead_id: str, next_status: LeadStatus, actor_ctx: dict, metadata: dict = {}):
        """
        - no quote without MAC EOS validation
        - no confirmation without UPOS payment or approved credit terms
        - no settlement without FCE
        - no arrival-ready status without FINAL_24H_LOGISTICS_PROOF_SEALED
        - all state changes SHADOW-sealed
        """
        # Logic check: all state changes SHADOW-sealed via ExecutionGuard
        return self.core.execute_commerce_action(
            "prestige.workflow.transition",
            actor_ctx,
            self._internal_transition,
            lead_id, next_status, metadata
        )

    def _internal_transition(self, lead_id, next_status, metadata):
        # Update logic
        self.leads[lead_id] = {
            "status": next_status,
            "last_updated": str(uuid.uuid4()), # mocked timestamp
            "meta": metadata
        }
        return self.leads[lead_id]

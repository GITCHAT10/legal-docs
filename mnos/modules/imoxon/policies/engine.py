class IdentityPolicyEngine:
    def __init__(self, identity_core):
        self.identity_core = identity_core

    def validate_action(self, action_type: str, context: dict):
        identity_id = context.get("identity_id")

        # Staff Binding requirements
        staff_actions = ["onboarding", "uniform_assignment", "linen_assignment", "delivery_acceptance"]
        if action_type in staff_actions:
            if not self._has_role(identity_id, "staff"):
                return False, "Action requires staff binding"

        # Hardened Verification requirements
        hardened_actions = ["hospitality.property.register", "sky_i.loop_cycle.finalize", "imoxon.vendor.approve"]
        if action_type in hardened_actions:
            if not self._is_verified(identity_id):
                 return False, f"CRITICAL ACTION: Identity {identity_id} must be verified (National ID / Biometric)"

        # Industry Partner / Special Discount Eligibility
        industry_actions = ["industry_discount_booking"]
        industry_roles = ["airline_partner", "medical_worker", "dmc_ta_staff", "club_member"]
        if action_type in industry_actions:
            if not any(self._has_role(identity_id, role) for role in industry_roles):
                return False, "Action requires specialized industry partner role"

        # Supplier Binding requirements
        supplier_actions = ["quote_submission", "contract_acceptance", "payout_receipt"]
        if action_type in supplier_actions:
            if not self._has_role(identity_id, "supplier"):
                return False, "Action requires supplier binding"
            if not self._is_verified(identity_id):
                return False, "Supplier must be verified"

        # Logistics Binding
        logistics_actions = ["shipment_intake", "warehouse_receipt", "dispatch_confirmation"]
        if action_type in logistics_actions:
            if not self._has_role(identity_id, "logistics_operator"):
                return False, "Action requires logistics binding"

        # Finance Binding
        finance_actions = ["manual_release_override", "refund_approval", "penalty_override"]
        if action_type in finance_actions:
            if not self._has_role(identity_id, "finance_operator") and not self._has_role(identity_id, "admin"):
                return False, "Action requires finance or admin binding"

        # Hard Rules
        if action_type == "asset_assignment" and not identity_id:
            return False, "No asset assignment without identity binding"

        if action_type == "payout" and not self._is_verified(identity_id):
            return False, "No supplier payout without verified supplier binding"

        return True, "Accepted"

    def _has_role(self, identity_id, role_name):
        if not identity_id:
            return False
        # Simplified check for demo
        profile = self.identity_core.profiles.get(identity_id)
        return profile and profile.get("profile_type") == role_name

    def _is_verified(self, identity_id):
        if not identity_id:
            return False
        profile = self.identity_core.profiles.get(identity_id)
        return profile and profile.get("verification_status") == "verified"

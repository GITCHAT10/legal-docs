class IdentityPolicyEngine:
    def __init__(self, identity_core):
        self.identity_core = identity_core

    def validate_action(self, action_type: str, context: dict):
        identity_id = context.get("identity_id")
        device_id = context.get("device_id")
        clearance_level = context.get("clearance_level", 1)

        # 1. ULTRA-PREMIUM / PROTOCOL POLICY (Level 4)
        if action_type.startswith("ultra.") or action_type == "imoxon.order.create_high_value":
            if clearance_level < 4:
                return False, f"FAIL CLOSED: Clearance Level 4 required for {action_type}"

            # IP Whitelisting (Simulated)
            if context.get("ip_address") and not self._is_ip_whitelisted(context.get("ip_address")):
                return False, "FAIL CLOSED: Access restricted to whitelisted IP for Level 4"

            # Biometric requirement (Simulated)
            if not context.get("biometric_verified"):
                return False, "FAIL CLOSED: Biometric verification required for Level 4 action"

        # 2. Dual Approval Enforcement for high value
        # This check is usually handled at the ExecutionGuard layer for state tracking,
        # but the policy engine defines the requirement.
        if action_type == "imoxon.payment.release_high_value" and context.get("amount", 0) >= 250000:
            if not context.get("is_second_approval"):
                 return False, "DUAL_APPROVAL_REQUIRED: Action requires a second signature from Clearance Level 4"

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
        if not identity_id: return False
        # Simplified check for demo
        profile = self.identity_core.profiles.get(identity_id)
        return profile and profile.get("profile_type") == role_name

    def _is_verified(self, identity_id):
        if not identity_id: return False
        profile = self.identity_core.profiles.get(identity_id)
        return profile and profile.get("verification_status") == "verified"

    def _is_ip_whitelisted(self, ip_address: str) -> bool:
        # Mock whitelist for demo
        whitelist = ["10.0.0.1", "127.0.0.1"]
        return ip_address in whitelist

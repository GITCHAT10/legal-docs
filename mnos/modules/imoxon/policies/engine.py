class IdentityPolicyEngine:
    def __init__(self, identity_core):
        self.identity_core = identity_core

    def validate_action(self, action_type: str, context: dict):
        identity_id = context.get("identity_id")
        device_id = context.get("device_id")
        role = context.get("role")

        # 1. PRESTIGE SUPPLIER PORTAL GATING
        if action_type.startswith("prestige.supplier"):
            if role == "mac_eos_admin":
                return True, "Admin override"

            if "approve" in action_type:
                if "finance" in action_type and role != "finance_reviewer":
                    return False, "Finance approval requires finance_reviewer role"
                if "revenue" in action_type and role != "revenue_reviewer":
                    return False, "Revenue approval requires revenue_reviewer role"
                if "cmo" in action_type and role != "cmo_reviewer":
                    return False, "CMO approval requires cmo_reviewer role"

            if "contract_upload" in action_type or "rate_submit" in action_type or "stop_sell" in action_type:
                if role != "supplier":
                    return False, "Action requires supplier role"

        # Legacy rules
        if action_type == "hospitality.property.register" and not self._is_verified(identity_id):
            return False, "Identity must be verified"

        return True, "Accepted"

    def _is_verified(self, identity_id):
        if not identity_id: return False
        profile = self.identity_core.profiles.get(identity_id)
        return profile and profile.get("verification_status") == "verified"

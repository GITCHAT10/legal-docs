class StaffOnboardingFlow:
    def __init__(self, identity_core):
        self.identity_core = identity_core

    def onboard_staff_batch(self, staff_list: list):
        results = []
        for staff in staff_list:
            # 1. Create Identity
            identity_id = self.identity_core.create_profile({
                "profile_type": "staff",
                "external_ref": staff.get("staff_code"),
                "full_name": staff.get("name"),
                "organization_id": staff.get("resort_id")
            })

            # 2. Record Consent
            self.identity_core.record_consent(identity_id, "data_usage")

            # 3. Bind Device
            device_id = self.identity_core.bind_device(identity_id, {"fingerprint": staff.get("device_hash")})

            # 4. Verify Identity (Simplified batch verification)
            self.identity_core.verify_identity(identity_id, "SYSTEM_ONBOARDER")

            # 5. Assign Role
            self.identity_core.assign_role(identity_id, "staff", {"resort_id": staff.get("resort_id")})

            results.append({
                "name": staff.get("name"),
                "identity_id": identity_id,
                "status": "ready"
            })

        return results

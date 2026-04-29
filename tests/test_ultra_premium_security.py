import unittest
import uuid
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.modules.finance.fce import FCEEngine
from mnos.shared.execution_guard import ExecutionGuard

class TestUltraPremiumSecurity(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowLedger()
        self.events = DistributedEventBus()
        self.fce = FCEEngine()
        self.identity = AegisIdentityCore(self.shadow, self.events)
        self.policy = IdentityPolicyEngine(self.identity)
        self.guard = ExecutionGuard(self.identity, self.policy, self.fce, self.shadow, self.events)

        with self.guard.sovereign_context():
            # Create Level 4 Actor
            self.admin_id = self.identity.create_profile({
                "full_name": "Ultra Admin",
                "profile_type": "admin",
                "clearance_level": 4,
                "biometric_hash": "BIO-VERIFIED-HASH"
            })
            self.admin_device = self.identity.bind_device(self.admin_id, {"fingerprint": "DEV-ADMIN"})

            # Create Level 1 Actor
            self.user_id = self.identity.create_profile({
                "full_name": "Standard User",
                "profile_type": "user",
                "clearance_level": 1
            })
            self.user_device = self.identity.bind_device(self.user_id, {"fingerprint": "DEV-USER"})

    def test_level_4_required_for_ultra_action(self):
        # Level 1 actor attempts ultra action
        ctx = {"identity_id": self.user_id, "device_id": self.user_device, "role": "user", "clearance_level": 1}
        with self.assertRaises(PermissionError) as cm:
            self.guard.execute_sovereign_action("ultra.package.create", ctx, lambda: True)
        self.assertIn("Clearance Level 4 required", str(cm.exception))

    def test_biometric_required_for_level_4(self):
        # Level 4 actor without biometric verification
        ctx = {
            "identity_id": self.admin_id,
            "device_id": self.admin_device,
            "role": "admin",
            "clearance_level": 4,
            "biometric_verified": False
        }
        with self.assertRaises(PermissionError) as cm:
            self.guard.execute_sovereign_action("ultra.package.create", ctx, lambda: True)
        self.assertIn("Biometric verification required", str(cm.exception))

    def test_ip_whitelist_enforced(self):
        # Level 4 actor from unauthorized IP
        ctx = {
            "identity_id": self.admin_id,
            "device_id": self.admin_device,
            "role": "admin",
            "clearance_level": 4,
            "biometric_verified": True,
            "ip_address": "192.168.1.1" # Not in whitelist [10.0.0.1, 127.0.0.1]
        }
        with self.assertRaises(PermissionError) as cm:
            self.guard.execute_sovereign_action("ultra.package.create", ctx, lambda: True)
        self.assertIn("Access restricted to whitelisted IP", str(cm.exception))

    def test_dual_approval_flow_high_value(self):
        # First actor initiates
        ctx1 = {
            "identity_id": self.admin_id,
            "device_id": self.admin_device,
            "role": "admin",
            "clearance_level": 4,
            "biometric_verified": True,
            "ip_address": "127.0.0.1",
            "amount": 300000
        }

        # Should return PENDING status
        result = self.guard.execute_sovereign_action("imoxon.payment.release_high_value", ctx1, lambda: "RELEASED")
        self.assertEqual(result["status"], "AWAITING_DUAL_APPROVAL")
        action_id = result["action_id"]

        # Same actor cannot approve second signature
        with self.assertRaises(PermissionError) as cm:
            self.guard.approve_second_signature(action_id, ctx1, lambda: "RELEASED")
        self.assertIn("requires a different actor", str(cm.exception))

        # Second actor (different Level 4)
        with self.guard.sovereign_context():
            admin2_id = self.identity.create_profile({"full_name": "Admin 2", "profile_type": "admin", "clearance_level": 4})
            admin2_dev = self.identity.bind_device(admin2_id, {"fingerprint": "DEV-ADMIN-2"})
        ctx2 = {
            "identity_id": admin2_id,
            "device_id": admin2_dev,
            "role": "admin",
            "clearance_level": 4,
            "biometric_verified": True,
            "ip_address": "127.0.0.1",
            "amount": 300000
        }

        # Final approval
        final_result = self.guard.approve_second_signature(action_id, ctx2, lambda: "RELEASED")
        self.assertEqual(final_result, "RELEASED")

if __name__ == "__main__":
    unittest.main()

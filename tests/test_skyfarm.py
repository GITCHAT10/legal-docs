import unittest
from skyfarm.identity.models import UserModel, Role, EntityModel, EntityType
from skyfarm.integration.service import create_integration_event, verify_signature, SECRET_KEY
import uuid

class TestSkyfarm(unittest.TestCase):
    def test_identity_models(self):
        user = UserModel(id="u1", username="captain1", role=Role.CAPTAIN, org_id="org1")
        self.assertEqual(user.username, "captain1")
        entity = EntityModel(id="v1", name="Sea Breeze", type=EntityType.VESSEL, owner_id="u1")
        self.assertEqual(entity.name, "Sea Breeze")

    def test_integration_signing(self):
        data = {"batch_id": "b1", "status": "harvested"}
        # create_integration_event(tenant_id, event_type, data, event_id=None)
        payload = create_integration_event("tenant1", "PRODUCTION", data, event_id="evt1")
        self.assertTrue(verify_signature(payload.model_dump(), SECRET_KEY))

        # Test invalid signature
        payload_dict = payload.model_dump()
        payload_dict["signature"] = "invalid"
        self.assertFalse(verify_signature(payload_dict, SECRET_KEY))

if __name__ == "__main__":
    unittest.main()

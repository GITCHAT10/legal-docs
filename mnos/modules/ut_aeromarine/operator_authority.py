from mnos.modules.ut_aeromarine.mission_schema import MissionType
from typing import Set

class OperatorAuthority:
    """
    UT AEROMARINE Operator Authority.
    Validates AEGIS-verified operators against specific mission types.
    """
    def __init__(self, identity_core):
        self.identity_core = identity_core
        self.authorities = {
            "MIG-ADMIN-01": {MissionType.QRD_RESPONSE, MissionType.SEARCH_AND_RESCUE, MissionType.RESORT_PATROL},
            "MALDIVES-MAPPING-01": {MissionType.ISLAND_MAPPING, MissionType.REEF_SURVEY}
        }

    async def has_authority(self, operator_id: str, mission_type: MissionType) -> bool:
        # Step 1: AEGIS Identity Check (Implicit via identity_core)
        if operator_id not in self.identity_core.profiles:
            return False

        # Step 2: Mission Type Authority
        allowed = self.authorities.get(operator_id, set())
        return mission_type in allowed

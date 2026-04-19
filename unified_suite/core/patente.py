import hashlib

class NexGenPatenteVerifier:
    """
    NEXGEN ASI PATENTE - Unified Authorization & Licensing System
    Verifies 'Patentes' (Licenses) for all airport and seaport operations.
    """

    @staticmethod
    def _get_secret():
        import os
        return os.getenv("NEXGEN_SECRET", "NEXGEN_SECRET_DEFAULT")

    @staticmethod
    def verify_patente(entity_id: str, patente_key: str, entity_type: str) -> bool:
        """
        Verifies if the entity has a valid NEXGEN PATENTE.
        Logic: A valid patente_key must match the SHA256 of entity_id + SECRET.
        """
        secret = NexGenPatenteVerifier._get_secret()
        expected_key = hashlib.sha256(f"{entity_id}:{secret}".encode()).hexdigest()
        return patente_key == expected_key

    @staticmethod
    def generate_patente(entity_id: str) -> str:
        """
        Generates a valid NEXGEN PATENTE for an entity.
        """
        secret = NexGenPatenteVerifier._get_secret()
        return hashlib.sha256(f"{entity_id}:{secret}".encode()).hexdigest()

    @staticmethod
    def authorize_access(entity_id: str, patente_key: str, area: str) -> bool:
        """
        PRODUCTION-GRADE AUTHORIZATION
        1. Verifies the SHA256 patente_key matches the entity_id + secret.
        2. Checks entity-based access control rules for the requested area.
        """
        # Step 1: Verification
        if not NexGenPatenteVerifier.verify_patente(entity_id, patente_key, "any"):
            return False

        # Step 2: Entity-based Access Control (EBAC)
        # Rules:
        # - Entities starting with 'CAPT' have access to 'DOCKING_AREA' and 'GATE_AREA'
        # - Entities starting with 'STAF' have access to 'GATE_AREA' only
        # - Entities starting with 'VESL' have access to 'DOCKING_AREA'
        # - Entities starting with 'FLGT' have access to 'GATE_AREA'

        if entity_id.startswith("CAPT"):
            return area in ["DOCKING_AREA", "GATE_AREA"]
        elif entity_id.startswith("STAF"):
            return area == "GATE_AREA"
        elif entity_id.startswith("VESL"):
            return area == "DOCKING_AREA"
        elif entity_id.startswith("FLGT"):
            return area == "GATE_AREA"

        return False

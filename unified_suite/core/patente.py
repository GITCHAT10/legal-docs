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
    def authorize_access(patente_key: str, area: str) -> bool:
        """
        Checks if the patente provides access to a specific port/airport area.
        For simulation: All valid patentes have access.
        """
        # Logic can be expanded to check specific scopes in the future
        return True

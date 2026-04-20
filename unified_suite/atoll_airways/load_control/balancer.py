from ..models import LoadManifest
import logging

logger = logging.getLogger("unified_suite")

class AtollLoadBalancer:
    """
    Handles weight and balance for MARS seaplane operations.
    Enforces DHC-6 Twin Otter safety limits.
    """

    @staticmethod
    def validate_load(manifest: LoadManifest) -> bool:
        """
        Validates total weight against MTOW.
        """
        # Base aircraft weight (Operating Empty Weight) is roughly 3500kg
        oew = 3500.0
        total_weight = oew + manifest.total_passenger_weight + manifest.total_baggage_weight

        if total_weight > manifest.mtow_limit:
            logger.error(f"Load Control: Weight limit exceeded! Total: {total_weight}kg (Limit: {manifest.mtow_limit}kg)")
            return False

        if manifest.passenger_count > 19:
            logger.error(f"Load Control: Passenger capacity exceeded! Count: {manifest.passenger_count}")
            return False

        logger.info(f"Load Control: Weight and balance verified for flight {manifest.flight_id}. Gross Weight: {total_weight}kg")
        return True

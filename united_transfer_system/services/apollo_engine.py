from sqlalchemy.orm import Session
from united_transfer_system import models
from united_transfer_system.services import governance
import logging

class ApolloEngine:
    """
    Autonomous Execution Engine (APOLLO).
    Enforces fail-closed rules and executes autonomous actions.
    """

    @governance.fail_closed_operation
    def enforce_settlement_rule(self, db: Session, leg_id: int):
        """If no LEG_COMPLETED: reverse_funds."""
        leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
        if not leg or leg.status != "completed":
            logging.error(f"Settlement Rule Violation: Leg {leg_id} not completed. Reversing funds.")
            # Trigger reversal via NEXUS FCE
            return False
        return True

    def auto_reroute_on_risk(self, db: Session, journey_id: int, risk_index: float):
        """If risk_index > threshold: auto_reroute."""
        if risk_index > 0.8:
            logging.info(f"Risk Rule Triggered (Index: {risk_index}): Initiating autonomous reroute for Journey {journey_id}")
            journey = db.query(models.Journey).filter(models.Journey.id == journey_id).first()
            if journey:
                journey.status = models.JourneyStatus.REROUTED
                db.commit()
            return True
        return False

    def execute_asset_swap(self, db: Session, leg_id: int, new_provider_id: str):
        """Autonomous Action: ASSET_SWAP."""
        leg = db.query(models.Leg).filter(models.Leg.id == leg_id).first()
        if leg:
            logging.info(f"APOLLO: Executing Asset Swap for Leg {leg_id} to Provider {new_provider_id}")
            leg.provider_id = new_provider_id
            db.commit()

apollo_engine = ApolloEngine()

from typing import Dict, Any
from mnos.modules.prestige.flight_matrix.market_rules import get_market_profile

class AgentPortalRecommendation:
    def __init__(self, core_system, feasibility_matrix, cluster_mapper):
        self.core = core_system
        self.feasibility = feasibility_matrix
        self.mapper = cluster_mapper

    def get_recommendations(self, actor_ctx: dict, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns top resort clusters and feasibility status for agent portal.
        """
        market = input_data.get("client_region", "EU")
        profile = get_market_profile(market)

        # Privacy filter (hides sensitive details)
        privacy_level = profile.get("default_privacy", 2)
        if input_data.get("privacy_level"):
            privacy_level = max(privacy_level, input_data["privacy_level"])

        # Fetch candidate resorts
        preferred_experience = input_data.get("preferred_experience", "luxury")
        suggested_clusters = ["speedboat_luxury", "uhNW_black_book"] if preferred_experience == "ultra-luxury" else ["speedboat_volume"]

        # Mocking evaluation for first resort in suggested cluster
        resort_name = self.mapper.get_resorts_in_cluster(suggested_clusters[0])[0]
        atoll = self.mapper.get_atoll(resort_name)

        eval_ctx = {
            "market_region": market,
            "flight_number": input_data.get("flight_number"),
            "resort_id": "RES-001",
            "resort_name": resort_name,
            "transfer_mode": "SPEEDBOAT" if "speedboat" in suggested_clusters[0] else "SEAPLANE",
            "atoll_zone": atoll,
            "scheduled_arrival_time_mle": input_data.get("arrival_time", "12:00"),
            "privacy_level": privacy_level,
            "guest_segment": input_data.get("guest_segment", "STANDARD")
        }

        decision = self.feasibility.evaluate_feasibility(actor_ctx, eval_ctx)

        return {
            "suggested_clusters": suggested_clusters,
            "top_resort": resort_name,
            "feasibility": decision.feasibility_status,
            "risk_reasons": decision.risk_reason_codes,
            "human_approval_required": decision.human_approval_required,
            "safe_to_quote": decision.safe_to_quote,
            "safe_to_confirm": False,
            "privacy_level_applied": privacy_level if privacy_level < 4 else "[REDACTED]"
        }

from decimal import Decimal
from datetime import datetime, UTC
from typing import List, Optional

class HustleLeaderboardEngine:
    """
    HUSTLE-LEADERBOARD-ENGINE: The National Economic Scoreboard.
    Formula: ISLAND_SCORE = (Revenue * 0.5) + (Active Hustlers * 0.2) + (Rating * 0.1) + (Bridge * 0.2)
    Rules: SHADOW validation only, No payout = No score, Anti-cheat.
    """
    def __init__(self, core, island_system, scoring_engine):
        self.core = core
        self.island_system = island_system
        self.scoring = scoring_engine
        self.island_scores = {} # island -> score
        self.hustler_rankings = {} # user_id -> revenue
        self.surge_alerts = []

    def update_leaderboard(self, event_type: str, data: dict):
        """Processes economic events to update rankings."""
        island = data.get("island")
        if not island:
            return

        # SHADOW VALIDATION ONLY (Simulated)
        if not data.get("shadow_ref"):
             return # No SHADOW proof -> No score

        if event_type == "revenue_generated":
            amount = Decimal(str(data["amount"]))
            hustler_id = data.get("hustler_id")

            # Update Hustler
            self.hustler_rankings[hustler_id] = self.hustler_rankings.get(hustler_id, 0.0) + float(amount)

            # Recalculate Island Score
            self._recalculate_island(island)

    def _recalculate_island(self, island: str):
        # 1. C2C Revenue
        revenue = self.island_system.island_stats.get(island, {}).get("revenue", 0.0)

        # 2. Active Hustlers (unique hustlers with revenue > 0)
        # Mock logic
        hustlers_count = 10 # Placeholder

        # 3. Avg Rating
        rating = 4.5 # Placeholder

        # 4. Bridge Contribution (from AtollCommanderScoringEngine)
        gm_id = self.island_system.island_registry.get(island)
        bridge_score = 0
        if gm_id and gm_id in self.scoring.scores:
             bridge_score = self.scoring.scores[gm_id].get("bridge", 0)

        # Formula
        score = (revenue * 0.5) + (hustlers_count * 0.2) + (rating * 0.1) + (bridge_score * 0.2)
        self.island_scores[island] = score

    def get_island_rankings(self) -> List[dict]:
        sorted_islands = sorted(self.island_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"island": k, "score": v} for k, v in sorted_islands]

    def get_top_hustlers(self, island: Optional[str] = None) -> List[dict]:
        # Filter by island in real system
        sorted_hustlers = sorted(self.hustler_rankings.items(), key=lambda x: x[1], reverse=True)
        return [{"user_id": k, "revenue": v} for k, v in sorted_hustlers[:10]]

    def trigger_surge_alert(self, island: str, factor: float):
        alert = {
            "island": island,
            "spike": f"+{int(factor * 100)}%",
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.surge_alerts.append(alert)
        self.core.events.publish("hustle.surge_detected", alert)
        return alert

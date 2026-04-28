import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List

class CanarySelector:
    """
    Production canary agent selection logic.
    Ensures deterministic and reproducible sampling for launch phases.
    """
    def __init__(self, seed: str = "MIG-AIG-SIG-2026Q2"):
        self.seed = seed

    def select_agents(self, agents: List[Dict[str, Any]], percentage: float = 0.10) -> List[Dict[str, Any]]:
        """
        Deterministic hash-based selection.
        """
        if not agents:
            return []

        selected = []
        # Calculate thresholds based on hash distribution
        scored_agents = []
        for agent in agents:
            hash_input = f"{agent['email']}:{agent.get('company', '')}:{self.seed}"
            score = int(hashlib.sha256(hash_input.encode()).hexdigest()[:8], 16)
            scored_agents.append((score, agent))

        scored_agents.sort(key=lambda x: x[0])
        limit = int(len(agents) * percentage)
        return [a[1] for a in scored_agents[:max(1, limit)]]

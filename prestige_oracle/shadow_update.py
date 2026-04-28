from typing import Dict, Literal
from scipy.stats import beta

class CompetencyBelief:
    """
    Bayesian Competency Updater using Beta Distribution.
    alpha (positives), beta_dist (negatives)
    """
    def __init__(self, alpha: float = 2.0, beta_dist: float = 2.0, pillar: str = "haccp"):
        self.alpha = alpha
        self.beta = beta_dist
        self.pillar = pillar

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        denom = (self.alpha + self.beta)**2 * (self.alpha + self.beta + 1)
        return (self.alpha * self.beta) / denom if denom > 0 else 0.0

    def update(self, event_type: Literal["positive", "negative", "neutral"], weight: float = 1.0):
        if event_type not in ("positive", "negative", "neutral"):
            raise ValueError("Invalid event_outcome. Must be 'positive', 'negative', or 'neutral'")
        if event_type == "positive":
            self.alpha += weight
        elif event_type == "negative":
            self.beta += weight

    def get_credible_interval(self, ci: float = 0.95) -> tuple:
        return beta.interval(ci, self.alpha, self.beta)

def process_shadow_event(
    current_beliefs: Dict[str, CompetencyBelief],
    event_pillar: str,
    event_outcome: Literal["positive", "negative", "neutral"],
    event_weight: float = 1.0
) -> Dict:
    belief = current_beliefs.get(event_pillar)
    if not belief:
        raise ValueError(f"Unknown pillar: {event_pillar}")

    belief.update(event_outcome, event_weight)

    return {
        pillar: {
            "mean": round(b.mean, 4),
            "variance": round(b.variance, 6),
            "ci_95": tuple(round(float(x), 4) for x in b.get_credible_interval())
        } for pillar, b in current_beliefs.items()
    }

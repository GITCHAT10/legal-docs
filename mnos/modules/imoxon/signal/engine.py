from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger()

class SignalEvent(BaseModel):
    contact_id: str
    channel: str # email, whatsapp, telegram, facebook, youtube, linkedin
    event_type: str # scraped, viewed, replied, clicked, opted_in
    payload: Dict[str, Any]
    signal_weight: float = 0.10
    risk_score: float = 0.30
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

class BayesianIntentScorer:
    """Calculates intent scores based on multi-channel signals."""
    def __init__(self, alpha=2.0, beta_param=5.0):
        self.alpha = alpha
        self.beta_param = beta_param
        self.weights = {
            "whatsapp_reply": 0.35,
            "telegram_reply": 0.30,
            "pdf_view": 0.25,
            "group_join": 0.20,
            "linkedin_accept": 0.18,
            "email_click": 0.14,
            "video_watch": 0.12,
            "profile_visit": 0.08
        }

    def calculate_score(self, history: List[SignalEvent]) -> float:
        evidence = sum(self.weights.get(f"{e.channel}_{e.event_type}", 0.10) for e in history)
        # Posterior mean of Beta distribution
        posterior_alpha = self.alpha + evidence * 10
        posterior_beta = self.beta_param + len(history)
        score = posterior_alpha / (posterior_alpha + posterior_beta)
        return round(score, 3)

class ThrottleManager:
    """Manages anti-ban rate limits per channel."""
    LIMITS = {
        'whatsapp': {'daily': 20, 'hourly': 3},
        'telegram': {'daily': 40, 'hourly': 6},
        'facebook': {'daily': 30, 'hourly': 5},
        'email_cold': {'daily': 20, 'hourly': 2}
    }

    def __init__(self):
        self.counters = {} # (account_id, channel) -> count

    def check_throttle(self, account_id: str, channel: str) -> bool:
        limit = self.LIMITS.get(channel, {'daily': 10})['daily']
        current = self.counters.get((account_id, channel), 0)
        return current < limit

    def record_activity(self, account_id: str, channel: str):
        key = (account_id, channel)
        self.counters[key] = self.counters.get(key, 0) + 1

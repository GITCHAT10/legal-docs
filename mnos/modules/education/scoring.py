from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, UTC
import hashlib
import json
from typing import Dict, Optional

class BlackCoralScoringEngine:
    """
    Black Coral Sovereign Index (BCSI) Engine - Pivot Version
    Weighting: 30% Academic Baseline / 70% Practical Verification (Quad-Stack)
    """

    # Practical Pillar Weights (sums to 1.0 within the 70% portion)
    PRACTICAL_WEIGHTS = {
        "haccp": Decimal("0.35"),
        "iso": Decimal("0.25"),
        "unesco": Decimal("0.20"),
        "michelin": Decimal("0.20")
    }

    ACADEMIC_WEIGHT = Decimal("0.30")
    PRACTICAL_WEIGHT = Decimal("0.70")

    TIER_THRESHOLDS = {
        "BCA": {"min_bcsi": 75, "min_haccp": 85},
        "BCO": {"min_bcsi": 85, "min_haccp": 95},
        "BCC": {"min_bcsi": 88, "min_haccp": 98},
        "BCD": {"min_bcsi": 90, "min_haccp": 100},
        "BCM": {"min_bcsi": 95, "min_haccp": 100}
    }

    def __init__(self, core):
        self.core = core

    def calculate_bcsi(self, trainee_id: str, practical_scores: Dict[str, float], academic_baseline: float = 0.0) -> Dict:
        """
        Compute BCSI using 30/70 formula.
        Final = (Academic * 0.3) + ( (HACCP*0.35 + ISO*0.25 + UNESCO*0.2 + MICHELIN*0.2) * 0.7 )
        """
        # 1. Calculate Practical Verification (Quad-Stack)
        haccp = Decimal(str(practical_scores.get("haccp", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iso = Decimal(str(practical_scores.get("iso", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        unesco = Decimal(str(practical_scores.get("unesco", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        michelin = Decimal(str(practical_scores.get("michelin", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        practical_total = (
            haccp * self.PRACTICAL_WEIGHTS["haccp"] +
            iso * self.PRACTICAL_WEIGHTS["iso"] +
            unesco * self.PRACTICAL_WEIGHTS["unesco"] +
            michelin * self.PRACTICAL_WEIGHTS["michelin"]
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Integrate Academic Baseline
        academic = Decimal(str(academic_baseline)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        bcsi_final = (
            academic * self.ACADEMIC_WEIGHT +
            practical_total * self.PRACTICAL_WEIGHT
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Hard Gate Check (HACCP must be >= 85)
        hard_gate_triggered = haccp < 85

        # 4. Determine Tier
        eligible_tier = None
        for tier, thresholds in sorted(self.TIER_THRESHOLDS.items(), key=lambda x: x[1]["min_bcsi"], reverse=True):
            if bcsi_final >= thresholds["min_bcsi"] and haccp >= thresholds["min_haccp"]:
                eligible_tier = tier
                break

        if not eligible_tier and bcsi_final >= 70:
            eligible_tier = "CORAL_ASSOCIATE"

        result = {
            "trainee_id": trainee_id,
            "bcsi_score": float(bcsi_final),
            "weighting": "30% Academic / 70% Practical",
            "breakdown": {
                "academic_baseline": float(academic),
                "practical_verification": float(practical_total),
                "pillars": {
                    "haccp": float(haccp),
                    "iso": float(iso),
                    "unesco": float(unesco),
                    "michelin": float(michelin)
                }
            },
            "eligible_tier": eligible_tier,
            "haccp_gate": "CLEAR" if not hard_gate_triggered else "HOLD",
            "calculated_at": datetime.now(UTC).isoformat()
        }

        # Anchoring to SHADOW
        from mnos.shared.execution_guard import _sovereign_context
        token = _sovereign_context.set({"token": "BCSI-PIVOT-CALC", "actor": {"identity_id": "SYSTEM", "system_override": True}})
        try:
            self.core.shadow.commit(
                "education.bcsi.calculated",
                trainee_id,
                result
            )
        finally:
            _sovereign_context.reset(token)

        return result

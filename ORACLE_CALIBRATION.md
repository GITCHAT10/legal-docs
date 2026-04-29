# 📊 PRESTIGE ORACLE: Calibration Roadmap (v1 → v2)

| Phase | Action | Expected Impact |
|-------|--------|----------------|
| **Week 1** | Collect 100+ SHADOW events + deployment outcomes | Validate Beta prior stability |
| **Week 2** | Tune logistic weights in `scoring.py` via grid search | ±10% probability calibration |
| **Week 3** | Add Redis rate limiter + async DB logging | Production-ready throughput |
| **Week 4** | Thompson sampling layer for EXMAIL | +15-22% conversion lift |

## Logistic Regression Tuning
We will use grid search to optimize the following weights in `scoring.py`:
- `manager_tier`
- `resort_complexity`
- `location_readiness`

Target Metric: Brier Score < 0.15 for success probability.

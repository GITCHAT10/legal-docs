# Model Validation Standard

## Required experiment record

Every experiment must record:

- hypothesis and economic rationale;
- authoring agent/model and version;
- code commit and dependency lock;
- dataset identifiers, licences, timestamps and checksums;
- train, validation and test periods;
- benchmark and acceptance thresholds;
- all attempted variants, including failures;
- fees, slippage, borrowing costs and latency assumptions;
- test results and reviewer decision.

## Walk-forward design

- Use chronological, non-overlapping train, validation and test windows.
- Keep the final holdout sealed until candidate selection is complete.
- Apply embargo/purging where labels overlap.
- Refit only at predefined boundaries.
- Report every fold; do not report only the best interval.

## Minimum evidence

- annualised return and volatility;
- Sharpe and Sortino ratios;
- maximum drawdown and recovery duration;
- expected shortfall and stress loss;
- turnover, capacity and liquidity utilisation;
- hit rate and payoff ratio;
- benchmark-relative return;
- stability across folds, assets and regimes;
- confidence intervals or bootstrap uncertainty;
- multiple-hypothesis adjustment.

## Automatic rejection conditions

Reject a candidate when any of the following is found:

- future information, label leakage or look-ahead bias;
- unlicensed or untraceable data;
- survivorship-biased universe without explicit correction;
- performance dependent on one fold, instrument or narrow period;
- implausible fills, costs, liquidity or borrow assumptions;
- missing failed-run history;
- unreproducible result;
- breach of a static invariant;
- undocumented model-generated dependency or code path.

## Independent validation

The validator must be independent of the candidate-generating agent. Production suitability requires a named human model-risk reviewer and Investment Committee approval.

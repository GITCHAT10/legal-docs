# AutoResearch Governance Standard

## 1. Purpose

This standard governs machine-generated investment research and code proposals within BLACKCORAL PRIME. It separates research experimentation from production investment operations.

## 2. Permitted agent activity

Agents may:

- formulate documented research hypotheses;
- generate candidate research code in an ephemeral sandbox;
- use approved, point-in-time datasets;
- run reproducible backtests and stress tests;
- compare candidates against a locked benchmark;
- prepare evidence packages for human review.

## 3. Prohibited agent activity

Agents must never:

- write to protected branches;
- approve or merge pull requests;
- change this governance folder or risk-policy files;
- access broker, exchange, bank, custodian, wallet or signing credentials;
- place, amend or cancel orders;
- deploy or upgrade smart contracts;
- determine investor eligibility;
- issue legal, tax, audit or regulatory conclusions;
- promote a research candidate directly to production;
- suppress failed experiments or adverse evidence.

## 4. Isolation requirements

Each experiment must run with:

- no production credentials;
- no outbound trading or settlement endpoint;
- read-only approved data access;
- ephemeral compute and filesystem;
- CPU, memory, runtime and cost limits;
- dependency allow-list and vulnerability scan;
- full prompt, model, code, data and environment lineage;
- deterministic seed where technically possible.

## 5. Candidate retention

Improved Sharpe ratio alone is insufficient. A candidate may be retained for review only when it passes all mandatory gates:

- out-of-sample performance;
- walk-forward stability;
- transaction costs and slippage;
- turnover and capacity;
- drawdown and tail loss;
- sensitivity and parameter stability;
- multiple-testing correction;
- data leakage and survivorship-bias checks;
- regime and liquidity stress;
- reproducibility by an independent runner.

Retention means “eligible for human review,” not “approved for deployment.”

## 6. Human authority

Only authorised humans may approve a research candidate for a separate implementation assessment. Approval must identify the precise commit, dataset snapshot, evidence bundle, permitted use, limits, expiry date and rollback conditions.

## 7. Change control

Changes to guardrails, validation thresholds or authority matrices require:

1. documented rationale;
2. legal/compliance review where applicable;
3. independent risk review;
4. Investment Committee or Board approval;
5. signed change record;
6. protected-branch review with no agent counted as an approver.

## 8. Vendor neutrality

Model interfaces must remain provider-neutral. No single model vendor may be treated as an authority. Outputs require corroboration, and materially different model results must be preserved as disagreement evidence.

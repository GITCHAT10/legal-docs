# Public Equity Analytics Governance Standard

Status: **Specification only — no live workflow, recommendation engine or trading integration**

## 1. Purpose

This standard governs a future daily public-equity analytics module for BLACKCORAL PRIME. The module may collect market data, calculate transparent indicators and prepare evidence-linked research memos for human review.

It must remain separate from order execution, custody, banking, token issuance and portfolio authority.

## 2. Approved initial scope

A future implementation may:

- read an approved ticker watchlist;
- retrieve end-of-day price and corporate-action data;
- calculate reproducible technical and risk measures;
- compare holdings to approved benchmarks;
- calculate indicative portfolio valuation changes;
- prepare a dated research memo;
- notify authorised reviewers that a memo is available.

It may not:

- place, amend or cancel an order;
- label an output “buy,” “sell” or “guaranteed”;
- infer missing fundamentals;
- overwrite historical memos;
- publish confidential holdings;
- treat a free data feed as authoritative without quality checks;
- use an LLM-generated figure without a source and timestamp.

## 3. Data-source controls

Free libraries and unofficial market-data sources are suitable for research prototypes only.

Each observation must record:

- provider and endpoint;
- retrieval timestamp and market timezone;
- raw versus adjusted value;
- currency;
- split and dividend treatment;
- exchange and ticker mapping;
- stale/missing-data status;
- reconciliation result against a second source for material decisions.

Corporate fundamentals must be taken from issuer filings, exchange disclosures or approved licensed datasets. Price history and fundamentals must not be silently mixed across incompatible dates.

## 4. Daily scheduling

“Market close” is exchange-specific. A single cron time is not sufficient for a multi-market portfolio.

A future scheduler must:

- define the exchange calendar for every ticker;
- handle holidays, early closes and daylight-saving changes;
- delay ingestion until the provider publishes completed bars;
- support idempotent reruns;
- prevent concurrent writes;
- retain the raw input snapshot and calculation version;
- fail closed when required data is missing or stale.

GitHub Actions is not guaranteed to run at an exact minute. Scheduled execution is a convenience trigger, not evidence that analysis completed on time.

## 5. Initial indicator set

Indicators are descriptive evidence, not decision authority:

- total return over 1, 5, 21, 63 and 252 trading days;
- 20/50/200-day moving averages;
- 14-period RSI;
- MACD (12, 26, 9);
- 20-day annualised volatility;
- 63-day beta to the approved benchmark;
- rolling maximum drawdown;
- average daily value traded;
- valuation and earnings fields only when sourced from dated issuer or licensed data.

No threshold may create an automatic transaction. Thresholds may only create a review flag.

## 6. Portfolio NAV analytics

A NAV layer may be designed only after the authoritative position source, FX source, valuation hierarchy and close policy are approved.

Indicative daily NAV must distinguish:

- official versus estimated prices;
- settled versus unsettled positions;
- base and local currencies;
- accrued income and fees;
- stale or fair-valued holdings;
- liquid listed assets versus private/RWA valuations.

The system must never combine live public-market prices with stale private-asset valuations without an explicit timestamp and valuation-status warning.

## 7. Memo controls

Every memo must include:

- “Research only — not an execution instruction”;
- data timestamp and market;
- source register;
- methodology version;
- missing/stale-data warnings;
- calculated indicators;
- material corporate events;
- uncertainty and contradictory evidence;
- named human reviewer;
- immutable memo ID and content hash.

## 8. Notifications

Email may notify authorised staff that a memo is ready. Discord and Telegram are not approved for confidential portfolio data or authoritative approvals.

No notification may contain credentials, full holdings, personal data, direct execution links or transaction-signing requests.

## 9. BlackRock example

BlackRock (NYSE: BLK) may be used as a test ticker, but any snapshot must be explicitly dated. Reported Q2 2026 figures—approximately $15.34 trillion AUM, $7.08 billion quarterly revenue, 45.9% adjusted operating margin and $13.91 adjusted EPS—are historical issuer-period data and must not be presented as live market data.

## 10. Promotion gate

Executable implementation requires:

1. approved ticker and benchmark register;
2. approved data licences and provider terms;
3. reproducible calculation tests;
4. market-calendar tests;
5. portfolio confidentiality review;
6. cybersecurity review;
7. legal/compliance review of outputs and distribution;
8. named operational owner;
9. Investment Committee approval;
10. separate repository suitable for executable code.

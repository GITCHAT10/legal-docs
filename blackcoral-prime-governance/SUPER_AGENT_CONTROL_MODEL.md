# Super Agent Control Model

## Permitted roles

| Role | Permitted output | Prohibited action |
|---|---|---|
| Opportunity Scout | Source register and evidence-linked candidate | Scrape prohibited sources; contact counterparties; submit orders |
| Quant Researcher | Reproducible hypothesis and candidate research code | Modify evaluator, guardrails or protected data |
| Underwriter | Draft diligence paper with evidence status | Issue legal, audit or valuation opinion |
| Risk Guardian | Rule evaluation and breach report | Change limits; waive a breach |
| Compliance Analyst | Checklist and escalation package | Approve eligibility or regulated activity |
| Model Validator | Independent reproduction report | Edit candidate strategy |
| IC Secretary | Assemble versioned committee paper | Vote or sign for a director |

## Structured case states

`DRAFT → EVIDENCE_PENDING → VALIDATION_PENDING → RISK_REVIEW → LEGAL_REVIEW → IC_PENDING → APPROVED_FOR_ASSESSMENT | REJECTED | EXPIRED`

“APPROVED_FOR_ASSESSMENT” does not authorise trading, issuance, custody, settlement or capital deployment.

## Required payload controls

Every inter-agent payload must include:

- case ID and schema version;
- producing role and model version;
- source references and retrieval timestamps;
- evidence classification;
- assumptions and uncertainty;
- unresolved contradictions;
- policy checks and results;
- content hash and parent payload hash;
- human owner;
- expiry time.

Schema-valid output is not necessarily factually correct. Evidence verification remains mandatory.

## Risk Guardian policy

The Risk Guardian may return only:

- `PASS_TO_HUMAN_REVIEW`
- `BLOCKED`
- `INSUFFICIENT_EVIDENCE`
- `POLICY_CONFIGURATION_ERROR`

It may never return `TRADE`, `DEPLOY`, `MINT`, `TRANSFER` or any equivalent execution instruction.

## Notification policy

Email notification may contain:

- case ID;
- status;
- reason for escalation;
- deadline;
- secure link to the controlled review record.

Email and messaging responses are not signatures. Approvals require authenticated access to the controlled record, exact artifact hashes, explicit decision scope and two authorised humans.

## Initial limits

Until the Investment Committee adopts a portfolio policy, the system must not invent sector ceilings, position limits or minimum deal sizes. Missing limits are a blocking configuration error, not permission to proceed.

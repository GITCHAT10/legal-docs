# MIG Anthropic-Class Model Policy

## Purpose

MIG Sovereign AI uses capability-based routing rather than binding business logic to marketing model names. Deployment aliases are mapped to model identifiers that are actually enabled in the connected Anthropic account.

## Capability tiers

| MIG tier | Intended work | Default control |
|---|---|---|
| FAST | extraction, classification, simple support | read-only tools |
| BALANCED | operational coordination and customer workflows | scoped adapters |
| DEEP_REASONING | finance, legal, coding and complex planning | human approval before consequential action |
| ULTRA_GUARDED | cybersecurity and executive-level analysis | isolated environment, human approval, no direct production writes |

The configuration may map these aliases to verified Haiku, Sonnet, Opus, Fable or Mythos-family deployments when those deployments are officially available to the account. Unknown or unavailable model names must fail closed.

## Reasoning policy

Reasoning budgets are allocated by workload and risk. Internal reasoning traces are not treated as an auditable business record. The auditable record is the task specification, evidence inputs, tool calls, approvals, outputs, policy decisions and hashes.

## Controlled improvement loop

The platform may:

1. evaluate agent results against fixed tests and business metrics;
2. generate candidate prompts, policies, code changes and test cases;
3. run candidates in isolated CI environments;
4. compare candidates against the current approved version;
5. open a pull request containing evidence and rollback instructions;
6. deploy only after authorized human review and passing controls.

The platform may not autonomously retrain or replace foundation models, modify approval requirements, disable audit logging, grant itself tools, merge its own pull requests, deploy directly to production, create external accounts or obtain unrestricted internet access.

## Cybersecurity containment

Cybersecurity agents operate only against explicitly authorized assets and targets. External network access is denied by default. Credentials are short-lived and scoped. All commands and artifacts are logged. Any target expansion, persistence, account creation or production mutation requires a separate approved task.

## Financial sovereignty

No model receives direct ledger write permission. Financial agents propose typed commands to governed adapters. The adapters enforce legal-entity boundaries, RBAC, idempotency, balanced entries, tax rules, limits, approvals and immutable audit events.

# Technology Assessment: AutoResearch, Super Agents, Git-Native Workflows and Scrypto

Status: **Governance assessment — not production approval**

## Executive decision

BLACKCORAL PRIME may study these technologies in isolated research environments, but none is approved for autonomous trading, custody, issuance, settlement, key management or production smart-contract deployment.

## 1. AutoResearch

### Decision: Conditional research approval

The useful pattern is a deliberately small editable surface, fixed experiment budget, locked evaluator and human-authored research instructions. It must not be interpreted as authority for a system to rewrite arbitrary investment or production code.

Required adaptation:

- one candidate module per experiment;
- fixed benchmark and sealed holdout;
- complete failed-run ledger;
- independent evaluator;
- no automatic merge or promotion;
- no trading credentials or execution endpoint;
- human approval after independent reproduction.

A higher Sharpe ratio is evidence for further review, not an investment decision.

## 2. Multi-agent frameworks

### Decision: Framework-neutral, limited pilot

CrewAI, AutoGen and LangGraph may be evaluated as orchestration libraries. BLACKCORAL governance must not depend on a specific framework.

Initial pilot ceiling:

- maximum 12 logical specialist roles;
- maximum 4 concurrent model calls per case;
- explicit task schemas and time/cost budgets;
- no peer agent may grant another agent additional authority;
- no agent may count as an independent reviewer of its own work;
- all disagreement and failed validation must be retained.

The phrase “100 agents” is a capacity aspiration, not an approved operating configuration.

## 3. Git-native workflow specifications

### Decision: Approve declarative schemas; reject repository vaults

Typed asset payloads and declarative workflows are appropriate for auditability. Git history alone is not an immutable decision ledger and must not be represented as one.

Never store encrypted private keys, dynamic secrets, seed phrases, signing material or custody credentials under `.swamp/vaults/` or elsewhere in Git. Encryption does not remove repository-distribution, retention and compromise risk.

Approved Git content:

- schemas;
- workflow definitions;
- policy references;
- hashes of externally stored evidence;
- non-secret environment requirements;
- signed approval references.

Required external controls:

- HSM or enterprise secrets manager;
- short-lived workload identity;
- environment-specific access policy;
- append-only external audit log;
- independent backup and recovery procedure.

## 4. Scrypto and Radix asset-oriented design

### Decision: Architecture research only

Scrypto’s resource-oriented model may reduce certain classes of accounting errors, but it does not create “zero risk,” guarantee legal title, establish regulatory compliance or eliminate all smart-contract vulnerabilities.

The proposed Bitcoin and RWA code must not be adopted because:

- “BC-BTC” could imply a Bitcoin-backed or yield-bearing product without custody, reserve, redemption and legal structure;
- an administrative badge is not equivalent to Board approval or multi-party institutional custody;
- component ownership and role design require formal threat modelling;
- the example accepts capital without investor eligibility, sanctions, subscription, valuation, allocation, redemption or emergency controls;
- ledger atomicity does not establish legal settlement finality;
- protocol and toolchain APIs require version-specific verification and testing.

No ticker, supply cap, mint authority or oracle connector may be hardcoded before a product legal opinion and formal product approval.

## 5. Notifications

### Decision: Email first; Telegram not approved for authoritative decisions

Notifications may announce that a research package is ready. They must not carry approval links that directly execute a trade or blockchain transaction.

Authoritative approval belongs in the controlled approval system with strong authentication, exact artifact hashes, expiry and dual-human authorization.

## 6. Required evidence before any executable pilot

- named business owner and accountable director;
- written research mandate;
- approved data sources and licences;
- threat model and abuse cases;
- model-risk validation plan;
- privacy and retention assessment;
- legal analysis of regulated activities;
- secrets and identity architecture;
- incident, rollback and kill-switch procedures;
- cost ceiling and termination criteria.

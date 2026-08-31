# E-LEGAL Freeze EF-05 — Maldives Legal Intelligence Core

**Owner:** Maldives International Group Pvt Ltd (MIG)  
**AI & Technology Layer:** Artificial Intelligence Group under the MIG brand  
**Authority Boundary:** AI = A0 decision support

## 1. Purpose

EF-05 is the authoritative legal-intelligence layer of E-LEGAL. It is designed to answer:

1. What is the authoritative source?
2. Which version was legally operative on the relevant date?
3. What binding or persuasive judicial authority interprets it?
4. Can each legal proposition and citation be verified?

## 2. Source registry

Every source must record:

- jurisdiction
- issuing/publishing authority
- source class
- canonical source URI
- publication date
- language
- translation status
- source-verification status
- full-text acquisition status
- immutable archive/hash status
- effective/commencement status
- supersession/repeal status

Source classes include:

- OFFICIAL_GAZETTE
- OFFICIAL_CONSOLIDATED_LAW
- OFFICIAL_COURT_JUDGMENT
- OFFICIAL_COURT_ORDER
- OFFICIAL_COURT_RULE
- OFFICIAL_REGULATOR_DOCUMENT
- OFFICIAL_TRANSLATION
- UNOFFICIAL_TRANSLATION
- AUTHORIZED_SECONDARY
- SECONDARY_COMMENTARY
- UNVERIFIED_EXTERNAL

## 3. Bitemporal legal model

E-LEGAL stores two timelines:

- legal validity: `valid_from`, `valid_to`
- system knowledge: `recorded_at`, `superseded_at`

Historical queries must never silently substitute current consolidated wording for the law in force on the requested date.

## 4. Amendment graph

Supported relationships include:

- AMENDS
- REPEALS
- SUBSTITUTES
- INSERTS
- DELETES
- RENUMBERS
- COMMENCES
- EXTENDS
- EXPIRES
- MADE_UNDER
- IMPLEMENTS

Stable provision UUIDs are used so renumbered provisions retain lineage.

## 5. Judicial precedent graph

Judicial hierarchy is modeled separately from legislation.

- Supreme Court
- High Court
- lower/trial courts

Precedent force is resolved relative to the target forum, later case treatment, majority status, issue match and decision status. AI similarity cannot create binding authority.

Case treatment edges include:

- CITES
- FOLLOWS
- APPLIES
- DISTINGUISHES
- AFFIRMS
- REVERSES
- OVERRULES
- LIMITS
- EXPLAINS
- REMANDS
- DISAPPROVES

AI may propose case treatment or ratio classification, but verified treatment requires authoritative support or human legal validation.

## 6. Dhivehi / English legal NLP

Dhivehi is first-class source text. E-LEGAL retains:

- original Dhivehi
- normalized searchable Thaana text
- bilingual alignment
- official English translation where available
- unofficial published translation where applicable
- machine translation as a separately labelled derivative

Machine translation can never masquerade as official translation.

## 7. Citation verification

Before a substantive citation passes the filing-readiness gate, the verifier checks:

1. source existence
2. identifier validity
3. exact provision/case resolution
4. applicable version and date
5. proposition support
6. majority/dissent status where relevant
7. supersession/repeal/later treatment
8. translation status
9. primary vs secondary authority

Unresolved citations fail closed.

## 8. Authority-first RAG

Retrieval sequence:

`jurisdiction -> as-of date -> document type -> authority class -> court hierarchy -> legal status -> lexical/semantic retrieval -> graph expansion -> rerank`

Vector similarity may assist retrieval but cannot outrank controlling primary authority.

## 9. Prompt-injection isolation

Retrieved legal documents are untrusted data, never instructions. Source text cannot override system policy, authorization boundaries or tool permissions.

## 10. Claim-level provenance

Material legal claims must retain:

- claim ID
- support classification
- exact source/version
- provision/paragraph
- source status
- retrieval snapshot
- human review state

Support classifications include:

- PRIMARY_DIRECT
- PRIMARY_INFERENTIAL
- MULTIPLE_PRIMARY_AUTHORITIES
- CONFLICTING_PRIMARY_AUTHORITY
- SECONDARY_CORROBORATION
- SECONDARY_ONLY
- NO_PRIMARY_SUPPORT

## 11. A0 authority boundary

AI may:

- research
- summarize
- compare
- translate
- analyze
- draft
- redline
- classify
- suggest
- flag risks
- generate research memoranda

AI may not:

- sign
- file with a court
- submit to government
- notarize
- certify translations/transcripts/tax outputs
- authorize escrow or payment
- waive conflicts or privilege
- accept clients autonomously
- make binding legal determinations
- impersonate lawyer/judge/notary/authorized human

## 12. Core fail-closed invariants

- Originals and source metadata are never overwritten by parsed/AI derivatives.
- Historical queries are version-aware.
- Gazette publication date is not automatically assumed to equal commencement date.
- Provisional consolidation cannot masquerade as verified law.
- Dissent cannot masquerade as majority holding.
- AI-proposed ratio cannot become VERIFIED_HOLDING automatically.
- An overruled/repealed status requires authoritative evidence.
- Fabricated/unresolved citations cannot pass filing readiness.
- Legal source freshness must be visible.
- A legal answer cannot claim CURRENT when authoritative source synchronization is stale.

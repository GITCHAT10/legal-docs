# BRAIN CORAL + MNOS Integration Contract

## Status

MAC EOS / iMOXON hardened security is the baseline. BRAIN CORAL and MNOS connect through the same AEGIS, ExecutionGuard, ShadowLedger and EventBus pattern. No intelligence or background system may bypass the sovereign action boundary.

## BRAIN CORAL role

BRAIN CORAL is a read-only intelligence and orchestration layer.

It may:

- read operational posture through governed APIs;
- receive audit-safe summaries and exception signals;
- queue governed action requests for review;
- emit intelligence events while inside ExecutionGuard.

It must not directly mutate:

- finance releases or refunds;
- procurement approvals or settlements;
- room inventory;
- identity records or role assignment;
- commerce orders or settlement postings.

## MNOS role

MNOS background syncs may use `authorized_context` only for legitimate internal operations such as dashboard refresh, health checks, sync completion, replay, or bootstrap. External MNOS users must still use verified identity, bound device, valid signature and policy validation.

## Audit requirements

Every governed BRAIN CORAL action must produce:

1. `*.intent`
2. `*.completed` or `*.failed`

Every internal MNOS sync must produce:

1. `mnos.internal.sync.completed`
2. EventBus publication to the `MNOS` partition

## New paths

- `GET /imoxon/brain-coral/status`
- `POST /imoxon/brain-coral/action-request`

## Test coverage

- BRAIN CORAL verified actor can read status.
- Non-BRAIN CORAL actor fails closed.
- Restricted mutation request fails closed.
- Safe action request is queued for governed review.
- MNOS internal sync uses `authorized_context` and writes audited records.

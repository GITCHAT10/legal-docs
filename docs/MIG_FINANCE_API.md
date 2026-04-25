# MIG FINANCE API SPECIFICATION

## Escrow
- `POST /v1/fce/escrow/lock`: Initialize financial lock.
- `POST /v1/fce/escrow/release`: Finalize payout upon event verification.

## Governance
- `POST /v1/governance/request`: Request multisig authorization.
- `POST /v1/governance/{id}/approve`: Submit role-based decision.

## Compliance Hooks
- `UT_JOURNEY_COMPLETE_HOOK`: Automatic settlement for mobility.
- `PROCUREMENT_GRN_HOOK`: Automatic settlement for supply chain.

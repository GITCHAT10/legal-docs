# 🏛️ SHADOW AUDIT CHAIN (MNOS 10.0)

## Core Doctrine
The SHADOW Ledger is a tamper-evident, hash-chained evidence store. It serves as the single source of truth for all sovereign operational and financial actions.

## Immutability Logic
- **Genesis-Seal**: The chain is anchored to a hardened root hash (`12890de2f...`) at Index 0.
- **SHA-256 Chaining**: Each entry includes the hash of the previous block, creating a linked timeline.
- **Deterministic Hashing**: Payloads are serialized canonical JSON before hashing to ensure forensic consistency.
- **Mutation-Evident**: Any post-event alteration to any block breaks the chain, detectable by automated boot checks and audit pulses.

## Audit Rules
- No deletions or edits permitted.
- Corrections must be recorded as new, linked reversal entries.
- Every commit requires a verified actor_id and objective_code.

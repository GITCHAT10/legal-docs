# Contract

- Read-only status must use ExecutionGuard.
- Restricted mutation requests must fail closed.
- Safe requests are queued for governed review.
- MNOS internal sync may use `authorized_context` only for system-owned flows.

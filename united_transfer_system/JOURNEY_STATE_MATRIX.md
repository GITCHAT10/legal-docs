# Journey State Matrix

The United Transfer ASI journey engine enforces a strict state machine. Out-of-order transitions are rejected by the `ExecutionGuard`.

| Current State | Valid Next States | Condition / Handshake |
|---------------|-------------------|------------------------|
| CREATED       | CONFIRMED, CANCELLED | API Confirmation |
| CONFIRMED     | DISPATCHED, CANCELLED | Resource Allocation |
| DISPATCHED    | PICKED_UP | QR1 Verification (Pickup) |
| PICKED_UP     | IN_TRANSIT | Departure Logged |
| IN_TRANSIT    | DROPPED | QR2 Verification (Drop) |
| DROPPED       | COMPLETED | Final Checks |
| COMPLETED     | PAID | Invoice Finalization + Payout |
| PAID          | (None) | Terminal State |
| CANCELLED     | (None) | Terminal State |

## Enforcement Rules
1. **Traceability**: Every state change must be accompanied by a `trace_id`.
2. **Identity**: Only AEGIS-verified operators can trigger state transitions.
3. **Atomic Transactions**: State changes and SHADOW audit entries are committed in a single atomic block.

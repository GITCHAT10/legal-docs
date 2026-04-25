# SOVEREIGN COMMERCE PROOF

## System Law: Fail-Closed
The iMOXON platform is now a sovereign execution engine. Every mutation is governed by the `ExecutionGuard`.

### 1. Guarded Execution
No mutation can occur without passing through `ExecutionGuard.execute_sovereign_action`.
- Validates Identity (AEGIS)
- Validates Device Binding
- Validates Role Policy
- Ensures Atomicity

### 2. Immutable Audit
Every action triggers two SHADOW entries:
1. `action.intent`: Logged before execution to record actor intent.
2. `action.completed` or `action.failed`: Logged after execution to record the result/error.

### 3. Financial Integrity
All pricing is centralized in `FCEEngine`.
- Enforces 10% Service Charge
- Enforces 17% TGST on Subtotal
- Mismatched or manual math is impossible.

### 4. Direct Call Blockade
- `EventBus.publish` rejects calls without an authorized guard context.
- `ShadowLedger.commit` rejects calls without an authorized guard context.
